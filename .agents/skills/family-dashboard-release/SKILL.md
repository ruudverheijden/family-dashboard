---
name: family-dashboard-release
description: Prepare and verify a Family Dashboard Docker Hub release, diagnose a failed release, or plan a Portainer rollback.
---

Read AGENTS.md and the release section of docs/DOCKER_HUB.md. Check the working tree and keep unrelated edits out of the release. Confirm that the intended numeric version matches the Dockerfile label and the /api/health response.

For an authorized publication, run the Release Docker Hub workflow on main with that version. Use the workflow run to confirm backend, container and browser results for the selected commit. Publication targets ruudv/family-dashboard, with a version tag and latest for Linux amd64 and arm64. Report the commit, workflow link and registry digest from the verification step.

If publication fails, establish which tags reached the registry and why the workflow failed before retrying. A retry of a failed publish job reuses its selected commit. Check for newer publications before retrying or moving latest. Keep Docker Hub credentials in GitHub Actions secrets.

For a rollback, follow the documented back-up and restore process and pin DASHBOARD_IMAGE to the previous working version or digest. Check compatibility of the stored data before rolling back. Treat a Portainer update as a separate operation.
