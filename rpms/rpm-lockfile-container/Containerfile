FROM registry.access.redhat.com/ubi9/ubi:latest

# Install dependencies
RUN dnf update -y && \
    dnf install -y git python3 python3-pip python3-dnf skopeo && \
    dnf clean all

RUN pip3 install https://github.com/konflux-ci/rpm-lockfile-prototype/archive/refs/tags/v0.16.0.tar.gz

ENTRYPOINT ["rpm-lockfile-prototype"]
