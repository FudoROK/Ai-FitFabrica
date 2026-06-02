#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "bootstrap_portable_host.sh must run as root" >&2
  exit 1
fi

if [[ ! -f /etc/os-release ]]; then
  echo "Cannot detect host OS; /etc/os-release is missing" >&2
  exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
OS_ID="${ID:-}"
OS_VERSION_CODENAME="${VERSION_CODENAME:-}"

if [[ "${OS_ID}" != "ubuntu" && "${OS_ID}" != "debian" ]]; then
  echo "Unsupported host OS: ${OS_ID}. Expected ubuntu or debian." >&2
  exit 1
fi

if [[ -z "${OS_VERSION_CODENAME}" ]]; then
  echo "Unsupported host OS: VERSION_CODENAME is missing." >&2
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings

if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
  curl -fsSL "https://download.docker.com/linux/${OS_ID}/gpg" -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
fi

ARCH="$(dpkg --print-architecture)"
cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${OS_ID} ${OS_VERSION_CODENAME} stable
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

TARGET_USER="${SUDO_USER:-}"
if [[ -n "${TARGET_USER}" ]]; then
  usermod -aG docker "${TARGET_USER}"
  echo "Added ${TARGET_USER} to the docker group. Re-login is required for group membership to apply."
fi

cat <<'EOF'
Portable host bootstrap complete.

Next steps:
1. Copy the repository to the target VM.
2. Create .env.portable-remote-staging.local from .env.portable-remote-staging.example.
3. Run python scripts/platform_foundation_smoke.py --env-file .env.portable-remote-staging.local --require-ready
4. Run bash scripts/deploy_portable_runtime.sh .env.portable-remote-staging.local
EOF
