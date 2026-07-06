# Lambda MicroVMs & Firecracker Research

## Official Sources

### AWS Lambda MicroVMs
- **Product page**: https://aws.amazon.com/lambda/lambda-microvms/
- **Launch announcement**: https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/ (June 22, 2026)
- **API Reference**: https://docs.aws.amazon.com/lambda/latest/microvm-api/
- **Developer Guide**: https://docs.aws.amazon.com/lambda/latest/dg/lambda-microvms-guide.html

### Firecracker (underlying technology)
- **GitHub**: https://github.com/firecracker-microvm/firecracker (35.3k stars)
- **Official docs**: https://firecracker-microvm.github.io/
- **Getting Started**: https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md

## Key Technical Facts

### Lambda MicroVMs Specifications
- **Architecture**: ARM64 support
- **Max resources**: 16 vCPUs, 32 GB memory, 32 GB disk
- **Max runtime**: 8 hours per session
- **Isolation**: Dedicated MicroVM per session, no shared kernel between users
- **State persistence**: Memory, disk, processes persist across sessions
- **Launch model**: Image-based with pre-initialized snapshots
- **Idle policy**: Configurable auto-suspension with `maxIdleDurationSeconds`, `suspendedDurationSeconds`, `autoResumeEnabled`
- **Authentication**: Short-lived tokens via `X-aws-proxy-auth` header

### Firecracker Specifications
- **Startup time**: <125 milliseconds
- **Memory overhead**: <5 MiB per microVM
- **Creation rate**: Up to 150 microVMs/second per host
- **Device model**: Only 5 emulated devices (virtio-net, virtio-block, virtio-vsock, serial console, keyboard controller)
- **Security**: KVM-based hardware virtualization + thread-specific seccomp filters + jailer process for cgroup/namespace isolation
- **Supported platforms**: Intel (Cascade Lake - Granite Rapids), AMD (Milan/Genoa), Arm Graviton 2-4
- **Guest OS**: Linux 4.14+, Amazon Linux 2/2023, Ubuntu 24.04

### API Operations (Lambda MicroVMs)
1. **Image Management**:
   - `CreateMicrovmImage` - Build image from Dockerfile + code artifact
   - `DeleteMicrovmImage`, `DeleteMicrovmImageVersion`
   - `GetMicrovmImage`, `GetMicrovmImageVersion`, `GetMicrovmImageBuild`
   - `ListMicrovmImages`, `ListMicrovmImageVersions`, `ListMicrovmImageBuilds`
   - `ListManagedMicrovmImages`, `ListManagedMicrovmImageVersions`
   - `UpdateMicrovmImage`, `UpdateMicrovmImageVersion`

2. **Lifecycle Control**:
   - `RunMicrovm` - Launch from image with idle policy
   - `SuspendMicrovm` - Manually suspend
   - `ResumeMicrovm` - Resume from suspended state
   - `TerminateMicrovm` - Terminate instance
   - `GetMicrovm` - Get status/details
   - `ListMicrovms` - List all instances

3. **Authentication**:
   - `CreateMicrovmAuthToken` - Generate access token
   - `CreateMicrovmShellAuthToken` - Generate shell access token

4. **Tagging**:
   - `TagResource`, `UntagResource`, `ListTags`

### Use Cases (from AWS)
- AI coding assistants (e.g., Claude Code, Cursor, GitHub Copilot Workspace)
- Interactive code environments
- Data analytics platforms
- Vulnerability scanners
- Game servers running user-supplied scripts
- Multi-tenant applications requiring per-user isolation

### Regional Availability (as of June 2026)
- US East (N. Virginia, Ohio)
- US West (Oregon)
- Europe (Ireland)
- Asia Pacific (Tokyo)

## Architecture Insights

### Image Build Process
1. User provides Dockerfile + code artifact (S3 URI)
2. Lambda builds Docker image, initializes application
3. Lambda creates snapshot of running environment state
4. Build logs stream to CloudWatch: `/aws/lambda/microvms/<image-name>`

### Base Images
- `arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1` (Amazon Linux 2023 minimal)
- Public ECR: `public.ecr.aws/lambda/microvms:al2023-minimal`

### Execution Model
- Each `RunMicrovm` call gets dedicated VM with unique endpoint URL
- JWE-based authentication per session
- Network routing and isolation handled by Lambda
- Auto-suspend on idle (configurable)
- Auto-resume on incoming request (optional)
- Suspended instances: no compute charges, reduced costs

## To Research Further
- [ ] Detailed pricing model (suspended vs. active vs. snapshot storage)
- [ ] Security model details (how auth tokens work, IAM integration)
- [ ] Networking capabilities (outbound access, VPC integration?)
- [ ] Monitoring and observability (CloudWatch integration)
- [ ] Error handling and retry behavior
- [ ] Snapshot restore time benchmarks
- [ ] Comparison with alternatives (AWS Fargate, ECS, Lambda Functions)
- [ ] Firecracker jailer configuration for production
- [ ] Real-world agent sandbox architecture patterns
- [ ] Resource limits and quotas

## Firecracker Jailer Security Model

### Isolation Mechanisms
- **Chroot jail**: Uses `pivot_root()` for filesystem isolation
- **Resource limits**: cgroups (v1/v2) + `setrlimit()` for CPU, memory, file descriptors
- **Privilege dropping**: Runs as specified uid/gid after setup
- **Namespace isolation**: Mount, PID, network namespaces
- **Device control**: Isolated `/dev/kvm` and `/dev/net/tun`

### Production Requirements (from prod-host-setup.md)
- **Security**:
  - Run via jailer with seccomp filters (default)
  - Dedicated non-privileged users per instance
  - Disable swap or use secure swap
  - Disable SMT (hyperthreading) to prevent side-channel attacks
  - Disable KSM (Kernel Samepage Merging) to prevent page deduplication attacks
  - Use DDR4 with TRR + ECC for Rowhammer protection
  - Block IMDS access (169.254.169.254) with nft/iptables

- **Performance**:
  - `quiet loglevel=1` on kernel command line (console logging adds 5ms+ to snapshot restore)
  - `favordynmods` in cgroupsv2 (Linux 6.1+)
  - Disable huge page recovery: `modprobe kvm nx_huge_pages=never`
  - Reduce timer interrupts: `modprobe kvm min_timer_period_us={value}`

- **Resource controls per instance**:
  - Memory: `memory.limit_in_bytes`, `memory.soft_limit_in_bytes`
  - CPU: `cpu.cfs_quota_us`
  - Disk I/O: `blkio.throttle.io_serviced`
  - File size: jailer's `fsize` limit

### Key Limitations
- Jailer creation time scales with host mount points (~10x slower with 500 mounts)
- Requires root execution (more capability than strictly needed)
- Manual cleanup required (can use `notify_on_release` with race condition awareness)
- PID stored in `<exec_file_name>.pid` in jail root

### Critical Caveat
"All inputs to the jailer are considered trusted" - operator must ensure parent directories are not writable by unprivileged users


## Live AWS Access for This Build

A real, working AWS profile is available for this course build: `AWS_PROFILE=poc`
(account `024989304407`, region `us-east-1`). It has genuine access to the
`aws lambda-microvms` CLI and Lambda MicroVMs is live in this account.

**Use this to capture REAL command output for chapters 4-16** instead of writing
hypothetical CLI output — this directly satisfies the "never fabricate output"
rule. Every drafting subagent for Parts II-V should:

1. `export AWS_PROFILE=poc` before running any `aws lambda-microvms ...` command.
2. Prefer reusing existing resources over creating new ones when the chapter's
   point doesn't require a fresh image build:
   - Existing image: `arn:aws:lambda:us-east-1:024989304407:microvm-image:lambda-microvms-poc-hello-world`
     (state UPDATED, latest active version 11.0) — good for RunMicrovm / GetMicrovm /
     auth token / suspend / resume / terminate examples.
   - Existing image: `arn:aws:lambda:us-east-1:024989304407:microvm-image:lambda-microvms-egress-test`
     (state UPDATED, version 13.0) — useful for chapters touching networking/egress.
   - Existing image: `arn:aws:lambda:us-east-1:024989304407:microvm-image:adam-microvm-image-test-1`.
3. **Always terminate any MicroVM you launch immediately after capturing its
   output** (`aws lambda-microvms terminate-microvm ...`) — this is a real,
   billable AWS account, not a sandbox. Never leave a running/suspended
   MicroVM behind. Verify with `list-microvms` that nothing is left running
   before finishing the chapter.
4. Only create a NEW microvm-image (`create-microvm-image`, which triggers a real
   Docker build) when the chapter is specifically about the image-build workflow
   (e.g. Chapter 4). Don't rebuild images gratuitously — image builds cost time
   and money and clutter the account with versions.
5. Redact the raw account ID (`024989304407`) from any output pasted into book
   HTML — replace with `<your-account-id>` or similar, the same way any AWS
   tutorial redacts account IDs, since account IDs in public docs pages are the
   kind of detail worth not publishing even though this course isn't being
   deployed publicly this run.
6. If a command requires a resource this account doesn't have permissions for,
   or the CLI errors, capture the real error text (redacted) rather than
   inventing a plausible-looking success — a real error is still real output.
