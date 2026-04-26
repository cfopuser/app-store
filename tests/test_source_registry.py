import os
import sys

sys.path.append(os.getcwd())

from core.sources.registry import create_source
from core.sources.aurora import AuroraSource
from core.sources.apkpure import APKPureSource
from core.sources.github import GitHubSource
from core.sources.apkcombo import APKComboSource


def test_create_source_apkpure():
    app_config = {"package_name": "com.example.app"}
    name, source, lookup = create_source("apkpure", app_config)

    assert name == "apkpure"
    assert isinstance(source, APKPureSource)
    assert lookup == "com.example.app"


def test_create_source_github_uses_repo_lookup():
    app_config = {"repo": "owner/repo"}
    name, source, lookup = create_source("github", app_config)

    assert name == "github"
    assert isinstance(source, GitHubSource)
    assert lookup == "owner/repo"


def test_create_source_aurora_uses_package_name():
    app_config = {"package_name": "com.example.app"}
    name, source, lookup = create_source("aurora", app_config)

    assert name == "aurora"
    assert isinstance(source, AuroraSource)
    assert lookup == "com.example.app"


def test_create_source_apkcombo():
    app_config = {"package_name": "com.example.app"}
    name, source, lookup = create_source("apkcombo", app_config)

    assert name == "apkcombo"
    assert isinstance(source, APKComboSource)
    assert lookup == "com.example.app"
