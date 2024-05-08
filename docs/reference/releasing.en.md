# Release Management

Kube-OVN currently mainly releases Minor and Patch versions. Minor versions include the addition of new features, major OVN/OVS upgrades, internal architecture adjustments, and API changes. Patch versions focus primarily on bug fixes, security vulnerability repairs, dependency upgrades, and are backward compatible with previous APIs.

## Maintenance Strategy

Kube-OVN currently continuously maintains the main branch and the two most recent release branches, such as `master`, `release-1.12`, and `release-1.11`. The latest release branch (e.g., `release-1.12`) will undergo more frequent iterations and releases, with all bug fixes, security vulnerabilities, and dependency upgrades being backported to this branch as much as possible.

The previous release branch (e.g., `release-1.11`) will backport significant bug fixes and security vulnerability repairs.

## Release Cycle

Minor versions are released as needed, based on whether there are significant new features or major architectural adjustments completed in the main branch, currently about once every six months. Patch versions are triggered based on the bug fix status of the branch, generally within a week after bug fixes are merged.

## Patch Version Release Method

Currently, most of the work for Patch versions can be automated using the [hack/release.sh](https://github.com/kubeovn/kube-ovn/blob/release-1.12/hack/release.sh) script, with the main steps described as follows:

1. Check the current branch build status (automated)
2. Push the new tag image to Docker Hub (automated)
3. Push the new tag code to GitHub (automated)
4. Update the version information in the code (automated)
5. Update the version information in the documentation repository (automated)
6. Generate Release Note PR (automated)
7. Merge Release Note (manual)
   1. Manually merge the GitHub action generated Release Note PR
8. Modify the GitHub Release information (manual)
   1. Edit the newly created Release on the GitHub Release page, change the title to the corresponding version number (e.g., `v1.12.12`), and copy the Release Note generated in the previous step into the Release details

## Minor Version Release Method

Currently, the main tasks for Minor branches still need to be completed manually, with the main steps described as follows:

1. Push a new release branch on GitHub, e.g., `release-1.13` (manual)
2. Update the version information in the `VERSION`, `dist/images/install.sh`, `charts/kube-ovn/values.yaml`, and `charts/kube-ovn/Chart.yaml` from the main branch to the next Minor version, e.g., `v1.14.0` (manual)
3. Push the new tag image to Docker Hub (manual)
4. Push the new tag code to GitHub in the release branch (manual)
5. Create a new release branch in the documentation repository, e.g., `v1.13`, and modify the `version` and `branch` information in the `mkdocs.yml` file (manual)
6. Generate Release Note PR (automated)
7. Merge Release Note (manual)
   1. Manually merge the GitHub action generated Release Note PR
8. Modify the GitHub Release information (manual)
   1. Edit the newly created Release on the GitHub Release page, change the title to the corresponding version number (e.g., `v1.13.0`), and copy the Release Note generated in the previous step into the Release details
9. Update the `VERSION` file in the release branch to the next Patch version, e.g., `v1.13.1`