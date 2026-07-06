# Course Outline: Building Agent Sandboxes with AWS Lambda MicroVMs

**Target Audience**: Backend developers new to VMs/containers
**Focus**: AWS Lambda MicroVMs (managed service)
**Language**: Python
**Use Cases**: AI agent code execution, untrusted scripts, security testing

## Part I: Foundations

### Chapter 1: Why Agent Sandboxes Matter
- The agent security problem: running untrusted code safely
- What can go wrong: filesystem access, network attacks, resource exhaustion
- Isolation spectrum: processes vs. containers vs. VMs
- When Lambda MicroVMs are the right choice
- **Try It**: Demonstrate an unsafe agent execution

### Chapter 2: Understanding Firecracker MicroVMs
- What makes Firecracker different from Docker and traditional VMs
- The five-device model: minimal attack surface
- KVM-based hardware virtualization explained for backend developers
- Performance characteristics: <125ms startup, <5 MiB overhead
- How Lambda leverages Firecracker for 15+ trillion invocations/month
- **Try It**: Explore Firecracker specs and architecture

### Chapter 3: Lambda MicroVMs Architecture
- Image-based deployment: Dockerfile → snapshot → instant launch
- State persistence across sessions (memory, disk, processes)
- The suspend/resume lifecycle
- Authentication model: JWE tokens and unique endpoint URLs
- How it differs from Lambda Functions
- **Try It**: Trace a MicroVM's lifecycle

## Part II: Getting Started with Lambda MicroVMs

### Chapter 4: Your First MicroVM Image
- Prerequisites: AWS account, IAM permissions, AWS CLI setup
- Writing a Dockerfile for the al2023-minimal base image
- Creating a simple Flask app as the MicroVM application
- Using `CreateMicrovmImage` to build and snapshot
- Watching build logs in CloudWatch
- **Challenge**: Build a "Hello, Sandbox" image

### Chapter 5: Launching and Connecting
- Using `RunMicrovm` with idle policies
- Understanding auth tokens with `CreateMicrovmAuthToken`
- Making your first authenticated request
- Inspecting MicroVM status with `GetMicrovm`
- Resource configuration: vCPUs, memory, disk
- **Challenge**: Launch and query your MicroVM

### Chapter 6: Lifecycle Management
- Manual suspend and resume operations
- Auto-suspension: `maxIdleDurationSeconds` and cost optimization
- State persistence: what survives suspension
- Graceful termination with `TerminateMicrovm`
- Handling failures and timeouts
- **Challenge**: Implement auto-suspend logic

## Part III: Building an Agent Sandbox

### Chapter 7: Executing Untrusted Code
- Designing a code execution API endpoint
- Receiving code snippets over HTTP
- Writing to filesystem, executing, capturing output
- Timeout handling and resource limits
- Security boundaries: what the MicroVM isolates
- **Challenge**: Build a Python code executor

### Chapter 8: Package Management and Dependencies
- Installing packages at runtime vs. baking into image
- Using pip/npm inside the MicroVM
- Handling version conflicts and dependency hell
- Caching strategies for faster execution
- Network access for package registries
- **Challenge**: Execute code that installs and uses a library

### Chapter 9: File System Isolation
- Understanding the MicroVM's filesystem
- Persistent storage across requests
- Cleaning up user-generated files
- Quota management and disk limits
- Reading uploaded files and artifacts
- **Challenge**: Build a file-based code runner

### Chapter 10: Resource Limits and Quotas
- CPU and memory configuration
- Preventing resource exhaustion attacks
- The 8-hour maximum runtime limit
- Per-request timeout patterns
- Monitoring resource usage
- **Challenge**: Enforce per-execution limits

## Part IV: Advanced Patterns

### Chapter 11: Multi-Tenant Isolation
- One MicroVM per user vs. shared MicroVMs
- Session management and routing
- Cost vs. security tradeoffs
- Cleaning state between users
- IAM roles and permissions per tenant
- **Challenge**: Build a multi-user sandbox

### Chapter 12: Security Hardening
- Network restrictions and egress control
- Dangerous operations to block
- Validating user code before execution
- Monitoring for malicious behavior
- Understanding Firecracker's security layers (KVM, seccomp, jailer)
- **Challenge**: Harden your sandbox against common attacks

### Chapter 13: Observability and Debugging
- CloudWatch integration for logs and metrics
- Tracing execution flow
- Debugging slow or failing executions
- Cost monitoring and optimization
- Health checks and error handling
- **Challenge**: Add comprehensive logging

### Chapter 14: Production Patterns
- Image versioning and updates
- Blue/green deployment for sandbox updates
- Scaling: when to launch more MicroVMs
- Error recovery and retry logic
- Designing for the 8-hour limit
- **Challenge**: Build a production-ready orchestrator

## Part V: Real-World Agent Systems

### Chapter 15: AI Coding Assistant Pattern
- How tools like Claude Code and Cursor use sandboxes
- Read-eval-print-loop in a MicroVM
- Managing long-running development sessions
- State preservation for incremental builds
- Integration with LLM tool calling
- **Challenge**: Build a minimal AI code assistant

### Chapter 16: Security Testing Sandbox
- Running vulnerability scanners safely
- Executing potentially malicious samples
- Network isolation for malware analysis
- Forensic snapshot preservation
- Automated teardown after analysis
- **Challenge**: Build a malware analysis pipeline

### Chapter 17: Beyond Lambda MicroVMs
- When to use self-hosted Firecracker instead
- Quick intro to Firecracker's REST API
- The jailer tool for production isolation
- Comparison with other sandboxing approaches (gVisor, Kata Containers)
- Future of MicroVM technology
- **Wrap Up**: Next steps for learning
