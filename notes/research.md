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

