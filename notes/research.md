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
4. Build logs stream to CloudWatch: `/aws/lambda-microvms/<image-name>` (verified
   live via `describe-log-groups` — see the Chapter 13 research section below;
   this line originally had the prefix wrong as `/aws/lambda/microvms/`)

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

## Chapter 12 (Security Hardening) citation reuse

Chapter 12 reused the KVM/seccomp/jailer research already captured above
("Firecracker Jailer Security Model" section) rather than re-deriving it, and
verified (live, 2026-07-06) that all four citation URLs used in the chapter
still resolve with HTTP 200:
- `https://firecracker-microvm.github.io/` &mdash; KVM framing quote and the
  jailer "second line of defense" quote, both confirmed present on the page.
- `https://github.com/firecracker-microvm/firecracker/blob/main/docs/jailer.md`
  &mdash; jailer disclaimer quote and flag mechanics (chroot via `pivot_root()`,
  `--cgroup`/`--resource-limit`, uid/gid drop), confirmed present.
- `https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md`
  &mdash; cgroup resource-limit specifics (`memory.limit_in_bytes`,
  `cpu.cfs_quota_us`, `blkio.throttle.io_serviced`), already captured above
  and reused rather than re-fetched line-by-line.
- `https://docs.aws.amazon.com/lambda/latest/dg/lambda-microvms-guide.html`
  &mdash; default network connectors (`HTTP_INGRESS`/`INTERNET_EGRESS`),
  same source already used in Chapter 7's egress-control research.

The chapter's application-level code scanner (`examples/ch12_code_scanner.py`,
`challenges/ch12.py`, `solutions/ch12.py`) is original to Chapter 12 and not
sourced from an external doc &mdash; it's framed explicitly in the chapter text
as the app-level complement to the OS-level KVM/seccomp/jailer layers, not a
restatement of them.

## Chapter 13 (Observability and Debugging) research

### CreateMicrovmImage `logging` parameter (confirmed live, 2026-07-06)

Fetched `https://docs.aws.amazon.com/lambda/latest/microvm-api/API_CreateMicrovmImage.html`
directly (not from memory) and confirmed the exact doc text, both on the
request parameter and the response element (identical wording in both
places):

> The logging configuration for build-time and runtime logs. Specify
> `{"cloudWatch": {"logGroup": "..."}}` to stream logs to a custom CloudWatch
> log group, or `{"disabled": {}}` to turn off logging.

Type: `Logging` object, a tagged union (only one member may be set) &mdash;
confirmed matching the `--logging` CLI shorthand already captured earlier in
this file (`{"cloudWatch": {"logGroup": "string", "logStream": "string"}}` or
`{"disabled": {}}`). Note the API doc's own example only shows `logGroup`
inside `cloudWatch`; `logStream` is accepted too (confirmed via `aws
lambda-microvms create-microvm-image help` in the CLI, captured earlier in
this file) but is optional &mdash; AWS auto-generates a log stream name per
build/run if omitted, which matches every real log-stream name observed
below (they're all `<version>/<uuid>` or `<date>[<version>]<microvm-id>`
patterns, never a name we supplied).

### Real CloudWatch Logs captured live from the `poc` account (2026-07-06)

`AWS_PROFILE=poc`, account `024989304407`, `us-east-1`. This account already
has real MicroVM image build/runtime logs flowing into CloudWatch from
earlier chapters' work &mdash; reused for Chapter 13 rather than generating
synthetic logs, per the "never fabricate output" rule.

- `aws logs describe-log-groups --log-group-name-prefix /aws/lambda-microvms`
  returns real log groups, one per image name, e.g.
  `/aws/lambda-microvms/lambda-microvms-poc-hello-world` (166478 bytes
  stored), `/aws/lambda-microvms/lambda-microvms-egress-test` (220042 bytes),
  `/aws/lambda-microvms/ch04-hello-sandbox`. Confirms Lambda MicroVMs creates
  one log group per *image name*, not per MicroVM instance or per build.
- `aws logs describe-log-streams --log-group-name
  /aws/lambda-microvms/lambda-microvms-poc-hello-world --order-by
  LastEventTime --descending` shows two real log-stream naming patterns in
  the same log group: `<version>/<request-uuid>` (build-time / early runtime
  streams, e.g. `11.0/0f34abe4-307a-4882-bb74-c34595e822cf`) and
  `<date>[<version>]microvm-<microvm-id>` (longer-running session streams,
  e.g. `2026/06/24[11.0]microvm-b510854e-5a9e-3da7-b55c-78980805c501`).
- `aws logs get-log-events` on the `11.0/0f34abe4-...` stream returns a real,
  ordinary FastAPI/uvicorn startup sequence:
  ```
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
  ```
- `aws logs get-log-events` on the `2026/06/24[11.0]microvm-b510854e-...`
  stream captured a **real failing execution** &mdash; a genuine Python
  traceback ending in `Exception: Control request timeout: initialize`,
  raised from `claude_agent_sdk/_internal/query.py` inside the sandboxed
  app. Real, not fabricated: this is an actual timeout that occurred during
  earlier course-build work in this same account, preserved in CloudWatch.
  Good honest example of "a failing execution's log output actually looks
  like this," including a full multi-frame traceback rather than a single
  clean error line.
- CloudWatch Logs Insights (`aws logs start-query` /
  `aws logs get-query-results`) works against these real log groups.
  `fields @timestamp, @message | filter @message like /Exception/ | sort
  @timestamp desc | limit 10` over the `lambda-microvms-poc-hello-world`
  group returned real matches spanning multiple sessions/days, including
  `Exception: Control request timeout: initialize` and
  `Exception: Claude Code returned an error result: success` &mdash; a second,
  distinct real failure mode, confirming that Insights queries scoped by
  `@message like /pattern/` are a practical way to find every failing
  execution across a log group without reading each stream by hand.
  Query statistics from a real run: `recordsMatched: 18`, `recordsScanned:
  2947`, `bytesScanned: 380376` over a 30-day window &mdash; small numbers,
  consistent with a low-traffic dev account, not fabricated round numbers.

### Real GetMicrovm fields relevant to health/error state (confirmed live)

`aws lambda-microvms get-microvm --microvm-identifier
microvm-29fabacb-68fe-30ed-b477-39bf36e55b16` on a terminated instance
returned a real `stateReason` field not previously captured in this file:
```json
"state": "TERMINATED",
"terminatedAt": "2026-07-05T21:47:36.936000-10:00",
"stateReason": "Success."
```
Confirms `GetMicrovm` carries a human-readable `stateReason` string
alongside `state` and (when applicable) `terminatedAt` &mdash; useful as a
first health-check signal without needing to open CloudWatch at all, since
polling `GetMicrovm` is cheaper than a Logs Insights query for "did this
instance end cleanly."

### CloudWatch metrics namespace

`aws cloudwatch list-metrics --namespace AWS/Lambda` and an unscoped
`list-metrics` call against the `poc` account returned **no** Lambda
MicroVMs-specific metrics namespace (only IAM/Logs/other pre-existing
resource dimensions from earlier chapters' work showed up as dimension
values, no actual metric namespace for MicroVM CPU/memory/invocations).
Do not claim a specific `AWS/LambdaMicroVMs` (or similar) CloudWatch metrics
namespace exists in the chapter &mdash; it wasn't observed live in this
account, and the developer guide page fetched for this chapter
(`lambda-microvms-guide.html`) doesn't document one either. Frame Chapter
13's "metrics" coverage around real, confirmed capabilities only: CloudWatch
*Logs* (confirmed above), Logs Insights queries over log content as the
practical substitute for dedicated metrics, and `GetMicrovm`/`ListMicrovms`
polling for state-based health signals. This is a real, honest gap worth
naming in the chapter rather than inventing metric names.

### Cost optimization

Reused from the developer guide's own framing (`lambda-microvms-guide.html`,
already fetched for Chapter 7/12, re-confirmed live 2026-07-06 for this
chapter): "MicroVMs can be suspended when idle, preserving memory and disk
state while reducing costs... You pay the baseline rate while your MicroVM
is running and only pay for active use above the baseline." Combine with
the idle-policy fields already captured in this file
(`maxIdleDurationSeconds`, `suspendedDurationSeconds`, `autoResumeEnabled`)
for the concrete cost-optimization mechanism: aggressive auto-suspend is the
primary cost lever Lambda MicroVMs exposes, not a separate cost-monitoring
API. No dedicated Cost Explorer / Budgets integration specific to Lambda
MicroVMs was found or claimed.

## Chapter 14 (Production Patterns) research

No new external facts were needed for this chapter beyond what earlier
chapters already captured and verified live against the `poc` account:

- Image versioning: reused the `imageVersion` field on a real `RunMicrovm`
  response (captured in the "Verified Real CLI Transcript" section above)
  and the `ListMicrovmImageBuilds` per-Graviton-generation build behavior
  (captured in the "Real ListMicrovmImageBuilds output" section above).
- 8-hour limit: reused `maximumDurationInSeconds: 28800` from the same real
  `RunMicrovm` transcript, and the `stateReason: "Success."` clean-termination
  field from Chapter 13's live `GetMicrovm` research.
- Idle-policy fields (`maxIdleDurationSeconds`, `suspendedDurationSeconds`,
  `autoResumeEnabled`) and the "no dedicated metrics namespace, no
  autoscaling" gap: reused from Chapter 13's research (confirmed live via
  `aws cloudwatch list-metrics` returning no MicroVMs-specific namespace).
- The blue/green cutover, retry-with-backoff, and scaling-heuristic code in
  `examples/ch14_orchestrator.py` is original to Chapter 14, framed
  explicitly in the chapter text as an orchestration pattern built from
  those primitives, not a restatement of an AWS-documented feature — Lambda
  MicroVMs has no built-in blue/green or autoscaling primitive of its own.

## Chapter 15 (AI Coding Assistant Pattern) research

### AWS's own framing of AI coding assistants as a Lambda MicroVMs use case

Fetched `https://aws.amazon.com/lambda/lambda-microvms/` directly (2026-07-06)
and confirmed an "AI coding assistants and agent sandboxes" section stating:
"AI-powered development tools generate and execute code on behalf of users,"
with the value proposition described as "a separate execution boundary per
task: an isolated compute environment with no access to agent state and no
shared state across users." No specific product (Claude Code, Cursor, GitHub
Copilot Workspace) is named on this page.

Also fetched the launch announcement,
`https://aws.amazon.com/blogs/aws/run-isolated-sandboxes-with-full-lifecycle-control-aws-lambda-introduces-microvms/`
(already in this file's Official Sources list) and confirmed it groups "AI
coding assistants" alongside "interactive code environments, data analytics
platforms, vulnerability scanners, and game servers that run user-supplied
scripts" as one sentence, again without naming a specific product.

**Important gap, stated explicitly rather than papered over**: no public
source found during this chapter's research confirms that any specific
hosted AI coding-assistant product's *cloud/remote* execution feature (e.g.
Claude Code's remote environments, Cursor's background agents) actually runs
on AWS Lambda MicroVMs internally, or on Firecracker directly, or on
anything else. AWS's own materials describe the use case category, not a
named customer's implementation. Chapter 15 states this gap explicitly
rather than implying a connection that isn't sourced.

### Claude Code's documented local sandbox (a different, but real and citable, architecture)

Fetched `https://code.claude.com/docs/en/sandboxing` live (2026-07-06,
redirected from `docs.claude.com/en/docs/claude-code/sandboxing` with a 301 —
the doc has moved hosts). Confirmed real, current detail:

- The sandboxed Bash tool is built into Claude Code and enforces filesystem
  and network isolation at the OS level for shell commands and their child
  processes.
- macOS uses the built-in Seatbelt framework; Linux and WSL2 use
  [bubblewrap](https://github.com/containers/bubblewrap) (confirmed live,
  200) for filesystem isolation plus `socat` for the network relay.
- Default write access is scoped to the working directory and the session
  temp directory (`$TMPDIR`); default read access is broad (the whole
  filesystem except denied paths), which is itself flagged in the docs as a
  reason to separately configure `sandbox.credentials` for files like
  `~/.aws/credentials` and `~/.ssh/`.
- Network access goes through a proxy with no domains pre-allowed by
  default; the first request to a new domain prompts for approval.
- "Subagents run in the same process as the parent session and use the same
  sandbox configuration" — confirms tool-calling and sandbox enforcement
  share one process/config in this specific product.

**Framing decision for Chapter 15**: this is real and citable, but it is OS-
level process sandboxing on the machine Claude Code already runs on (Seatbelt/
bubblewrap), not a MicroVM/VM boundary. The chapter states this distinction
explicitly rather than implying Claude Code's local sandbox is evidence about
Lambda MicroVMs or Firecracker specifically.

### Cursor — no public infrastructure detail found

Attempted `https://cursor.com/blog/background-agents` (404, page doesn't
exist at that path), `https://cursor.com/blog/agent-web` (200, but content is
about UX/accessibility of background agents, not infrastructure — no
mention of VMs, containers, or sandboxing internals), and
`https://docs.cursor.com/background-agent` (redirects to `cursor.com/docs`,
a docs homepage with no specific infrastructure content surfaced). No public
source was found describing Cursor's background-agent execution environment
at an infrastructure level. Chapter 15 does not make any specific claim
about Cursor's internal architecture as a result — it's named only in the
generic "tools like Claude Code and Cursor" framing that AWS's own materials
use for the use-case category, not with any product-specific architecture
claim attached.

### Example script and challenge

`examples/ch15_repl_session.py`, `challenges/ch15.py`, and `solutions/ch15.py`
are original to Chapter 15, not sourced from an external doc. The chapter
text and the script's own docstring both state explicitly that `Session` is
a local simulation (a temp directory plus scoped `subprocess` calls) of a
MicroVM boundary, not a real VM — consistent with how Chapter 11's
`MockMicrovmClient` and Chapter 14's `BlueGreenOrchestrator` example already
handled the same "simulate the API shape, not the network" pattern for
scenarios that don't need a live AWS call to teach the point.

## Chapter 16 (Security Testing Sandbox) research

### INetSim — fake-internet simulator for malware analysis (verified 2026-07-06)

Fetched `https://www.inetsim.org/` (HTTP 200, live) and confirmed:

> "INetSim is a software suite for simulating common internet services in a
> lab environment, e.g. for analyzing the network behaviour of unknown malware
> samples."

INetSim provides simulated DNS, HTTP/HTTPS, SMTP, FTP, and other services so
that malware samples in a sandboxed environment can attempt C2 callbacks,
download payloads, or exfiltrate data against fake services that log everything
without allowing real internet access. This is the standard companion tool
paired with sandbox detonation environments (Cuckoo Sandbox, FLARE VM, REMnux)
in malware-analysis lab setups.

Live-verified URL used in Chapter 16 HTML:
- `https://www.inetsim.org/` — project homepage, confirmed 200 on 2026-07-06.

### RFC 5737 TEST-NET addresses (not re-verified — well-known IETF standard)

The example script uses `192.0.2.1` (TEST-NET-1, RFC 5737) as the destination
for the synthetic sample's blocked outbound connection attempt. This is a
documentation/example address block that routes nowhere on the real internet,
making it safe to use as a stand-in for a C2 server address without any risk
of hitting a real host. No verification needed — this is a permanent IANA
reservation documented in RFC 5737 (January 2010).
