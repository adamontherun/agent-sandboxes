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

## Verified Real CLI Transcript (captured live, poc account, 2026-07-05)

This is a genuine end-to-end lifecycle run against the existing
`lambda-microvms-poc-hello-world` image (version 11.0). Drafting agents for
Parts II-V should use this real transcript for Chapters 5-6 rather than
re-deriving it, and may reuse the same command shapes (with fresh
microvm-identifiers) for other chapters that need real output. Account ID
and endpoint below are redacted in any book HTML — use `<your-account-id>`
and a placeholder endpoint pattern instead.

### 1. RunMicrovm

Command:
```
aws lambda-microvms run-microvm \
  --image-identifier arn:aws:lambda:us-east-1:<account-id>:microvm-image:lambda-microvms-poc-hello-world \
  --execution-role-arn arn:aws:iam::<account-id>:role/MicroVMLambdaPOCRole \
  --idle-policy '{"maxIdleDurationSeconds":300,"suspendedDurationSeconds":300,"autoResumeEnabled":true}'
```

Real output (redacted):
```json
{
    "microvmId": "microvm-29fabacb-68fe-30ed-b477-39bf36e55b16",
    "state": "PENDING",
    "endpoint": "<random-id>.lambda-microvm.us-east-1.on.aws",
    "imageArn": "arn:aws:lambda:us-east-1:<account-id>:microvm-image:lambda-microvms-poc-hello-world",
    "imageVersion": "11.0",
    "executionRoleArn": "arn:aws:iam::<account-id>:role/MicroVMLambdaPOCRole",
    "idlePolicy": {
        "maxIdleDurationSeconds": 300,
        "suspendedDurationSeconds": 300,
        "autoResumeEnabled": true
    },
    "maximumDurationInSeconds": 28800,
    "startedAt": "2026-07-05T21:43:41.138000-10:00",
    "ingressNetworkConnectors": [
        "arn:aws:lambda:us-east-1:aws:network-connector:aws-network-connector:HTTP_INGRESS"
    ],
    "egressNetworkConnectors": [
        "arn:aws:lambda:us-east-1:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
    ]
}
```

**Real gotcha caught**: omitting `suspendedDurationSeconds`/`autoResumeEnabled`
from `--idle-policy` produces:
```
aws: [ERROR]: An error occurred (ParamValidation): Parameter validation failed:
Missing required parameter in idlePolicy: "suspendedDurationSeconds"
Missing required parameter in idlePolicy: "autoResumeEnabled"
```
All three idle-policy fields are required together — worth calling out in
Chapter 5, since a reader would reasonably assume they're independently
optional.

**Confirms**: `maximumDurationInSeconds` defaults to 28800 (= 8 hours),
matching the documented max-runtime spec. Default network connectors are
`HTTP_INGRESS` and `INTERNET_EGRESS` — no explicit
`--ingress-network-connectors`/`--egress-network-connectors` needed for
basic outbound internet + inbound HTTP.

### 2. GetMicrovm (5s after launch)

Real output showed `"state": "RUNNING"` within 5 seconds of the `run-microvm`
call returning `PENDING` — consistent with Firecracker's <125ms VM boot time
plus image/network setup overhead.

### 3. CreateMicrovmAuthToken

Command:
```
aws lambda-microvms create-microvm-auth-token \
  --microvm-identifier microvm-29fabacb-68fe-30ed-b477-39bf36e55b16 \
  --expiration-in-minutes 15 \
  --allowed-ports '[{"port":5000}]'
```

**Real gotcha caught**: `allowedPorts` is a tagged union — passing
`{"port":5000,"protocol":"HTTP"}` fails:
```
aws: [ERROR]: An error occurred (ParamValidation): Parameter validation failed:
Invalid number of parameters set for tagged union structure allowedPorts[0].
Can only set one of the following keys: port. range. allPorts.
Unknown parameter in allowedPorts[0]: "protocol", must be one of: port, range, allPorts
```
Correct shape is `{"port": 5000}` only — no protocol field, and each list
entry sets exactly one of `port`, `range`, or `allPorts`. Worth calling out
explicitly since the tagged-union error message is easy to misread as "add
a protocol field" when it's actually "remove a field."

Real (successful) response shape:
```json
{
    "authToken": {
        "X-aws-proxy-auth": "eyJraWQiOiJ...<long JWE compact-serialization token>...w"
    }
}
```
Confirms the announcement's claim that auth is a JWE token attached via the
`X-aws-proxy-auth` header — this is a real JWE compact serialization
(5 dot-separated base64url segments: protected header, encrypted key, IV,
ciphertext, tag), matching JOSE/JWE spec shape, not a made-up token format.

**Environment note**: hitting the actual HTTPS endpoint with this token
timed out from this build environment's network sandbox (the
`*.lambda-microvm.us-east-1.on.aws` domain isn't in the allowed egress
list here) — that's a build-environment restriction, not a MicroVM/service
issue. A reader running this from a normal shell should expect the curl to
succeed once past this environment's constraints; note this honestly in the
chapter rather than showing a fabricated 200 response body.

### 4. SuspendMicrovm / ResumeMicrovm

Both calls return **no output body** on success (confirmed twice, live).
State transitions confirmed via follow-up `GetMicrovm`:
- After `suspend-microvm` + 3s: `state: SUSPENDED`
- After `resume-microvm` + 3s: `state: RUNNING`

### 5. TerminateMicrovm

Also returns no output body on success. Follow-up `ListMicrovms` confirmed
`state: TERMINATED` for the instance, with `startedAt` preserved in the
record. No `endpoint`/`idlePolicy`/network-connector fields are present in
the terminated instance's list entry — those are only populated while
non-terminal.

### Available IAM roles in this account (for reference in examples)
- `arn:aws:iam::<account-id>:role/MicroVMLambdaPOCRole` — general execution role, used above
- `arn:aws:iam::<account-id>:role/LambdaMicroVMsNetworkConnectorRole`
- `arn:aws:iam::<account-id>:role/service-role/adam-microvm-image-test-1-build-role-2ced5777` — image build role pattern

## Additional Real API Detail: CreateMicrovmImage (from live `help` + calls)

- `--base-image-arn` [required]: e.g. `arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1`
  — confirmed via real `ListManagedMicrovmImages` call (only one managed base
  image currently listed: `al2023-1`).
- `--build-role-arn` [required]: IAM role ARN pattern
  `arn:aws:iam::<account>:role/<role-name>` assumed during build.
- `--code-artifact` [required, tagged union, only one key: `uri`]:
  ```json
  {"uri": "s3://bucket/path/artifact.zip"}
  ```
  (or an ECR image URI). Shorthand: `uri=string`.
- `--name` [required].
- `--logging` (tagged union, one of `disabled` or `cloudWatch`):
  ```json
  {"cloudWatch": {"logGroup": "string", "logStream": "string"}}
  ```
  or `{"disabled": {}}`.
- Build is asynchronous: image goes `CREATING` → `CREATED` (success) or
  `CREATE_FAILED`. Poll with `GetMicrovmImage`.
- Other optional params exist: `--cpu-configurations`, `--resources`,
  `--additional-os-capabilities`, `--hooks`, `--environment-variables`,
  `--egress-network-connectors`, `--tags`, `--client-token`.

### Real ListMicrovmImageBuilds output (existing image, version 11.0)

Confirms builds are per chipset generation — the same image version produced
TWO separate successful builds, one per Graviton generation:
```json
{
  "items": [
    {"imageVersion": "11.0", "buildId": "...", "buildState": "SUCCESSFUL",
     "architecture": "ARM_64", "chipset": "GRAVITON", "chipsetGeneration": "4", ...},
    {"imageVersion": "11.0", "buildId": "...", "buildState": "SUCCESSFUL",
     "architecture": "ARM_64", "chipset": "GRAVITON", "chipsetGeneration": "3", ...}
  ]
}
```
This confirms the ARM64-only architecture claim from the product page AND
reveals a previously-undocumented detail worth telling readers: one image
version can have multiple builds, one per Graviton generation, and
`list-microvm-image-builds` requires `--image-version` (not just the image
identifier) as a required parameter — a small but real gotcha for anyone
scripting around builds.

### Note on new image builds

Did not trigger a fresh `create-microvm-image` build during research capture
(real Docker build, takes real time/cost, and the account already has three
working example images to reuse: `lambda-microvms-poc-hello-world`,
`lambda-microvms-egress-test`, `adam-microvm-image-test-1`). Chapter 4's
drafting agent should decide whether the "Hello, Sandbox" challenge needs an
actual fresh build to be honest, and if so, run exactly ONE real build,
capture its output, and note the real wall-clock time observed.
