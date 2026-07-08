//! Native create path for asv_env_rattler using the rattler crate stack.
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::path::PathBuf;

use rattler::install::Installer;
use rattler_conda_types::{Channel, ChannelConfig, MatchSpec, ParseStrictness, Platform};
use rattler_repodata_gateway::Gateway;
use rattler_solve::{ChannelPriority, RepoDataIter, SolverImpl, SolverTask, resolvo::Solver};
use rattler_virtual_packages::{VirtualPackage, VirtualPackageOverrides};
use url::Url;

fn runtime_err(msg: impl ToString) -> PyErr {
    PyRuntimeError::new_err(msg.to_string())
}

/// Create a conda-style prefix using in-process rattler solve+install.
#[pyfunction]
#[pyo3(signature = (prefix, python_version, channels, extra_specs=None))]
fn create_prefix(
    prefix: &str,
    python_version: &str,
    channels: Vec<String>,
    extra_specs: Option<Vec<String>>,
) -> PyResult<()> {
    let prefix = PathBuf::from(prefix);
    let mut specs: Vec<String> = vec![
        format!("python={}", python_version),
        "pip".into(),
        "wheel".into(),
    ];
    if let Some(extra) = extra_specs {
        specs.extend(extra);
    }
    let channels = if channels.is_empty() {
        vec!["conda-forge".to_string()]
    } else {
        channels
    };

    let rt = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| runtime_err(format!("tokio runtime: {e}")))?;

    rt.block_on(async move {
        create_prefix_async(&prefix, &channels, &specs)
            .await
            .map_err(runtime_err)
    })
}

async fn create_prefix_async(
    prefix: &std::path::Path,
    channels: &[String],
    specs: &[String],
) -> Result<(), String> {
    let platform = Platform::current();
    let channel_config = ChannelConfig::default_with_root_dir(
        std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
    );

    let channel_list: Result<Vec<Channel>, String> = channels
        .iter()
        .map(|c| {
            if let Ok(url) = Url::parse(c) {
                Ok(Channel::from_url(url))
            } else {
                Channel::from_str(c.as_str(), &channel_config).map_err(|e| e.to_string())
            }
        })
        .collect();
    let channel_list = channel_list?;

    let match_specs: Result<Vec<MatchSpec>, String> = specs
        .iter()
        .map(|s| MatchSpec::from_str(s, ParseStrictness::Lenient).map_err(|e| e.to_string()))
        .collect();
    let match_specs = match_specs?;

    let gateway = Gateway::new();
    let repodata_list = gateway
        .query(
            channel_list.iter().cloned(),
            [platform, Platform::NoArch],
            match_specs.iter().cloned(),
        )
        .recursive(true)
        .execute()
        .await
        .map_err(|e| format!("repodata query: {e}"))?;

    // Own records so both the solver and installer can use them.
    let owned_records: Vec<_> = repodata_list
        .iter()
        .flat_map(|rd| rd.iter().cloned())
        .collect();

    let virtual_packages = VirtualPackage::detect(&VirtualPackageOverrides::default())
        .map_err(|e| format!("virtual packages: {e}"))?
        .into_iter()
        .map(Into::into)
        .collect();

    let task = SolverTask {
        available_packages: vec![RepoDataIter(owned_records.iter())],
        locked_packages: vec![],
        pinned_packages: vec![],
        virtual_packages,
        specs: match_specs,
        constraints: vec![],
        timeout: None,
        channel_priority: ChannelPriority::Strict,
        exclude_newer: None,
        strategy: Default::default(),
        dependency_overrides: vec![],
        cancellation_token: None,
    };

    let mut solver = Solver;
    let solved = solver
        .solve(task)
        .map_err(|e| format!("solve failed: {e}"))?;

    std::fs::create_dir_all(prefix).map_err(|e| format!("mkdir prefix: {e}"))?;

    Installer::new()
        .install(prefix, solved.records)
        .await
        .map_err(|e| format!("install failed: {e}"))?;

    Ok(())
}

#[pyfunction]
fn backend_name() -> &'static str {
    "rattler-crates"
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_prefix, m)?)?;
    m.add_function(wrap_pyfunction!(backend_name, m)?)?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
