# Building Agent Sandboxes with AWS Lambda MicroVMs

Learn how to safely execute untrusted code in isolated environments using AWS Lambda MicroVMs and Firecracker. This course covers building production-ready agent sandboxes for AI coding assistants, security testing, and multi-tenant applications.

[![Read the Book](https://img.shields.io/badge/📖_Read_the_Book-adamontherun.github.io/agent--sandboxes-c0392b)](https://adamontherun.github.io/agent-sandboxes/)

[![Building Agent Sandboxes book cover — the title, intro paragraph, and the sidebar table of contents](book/assets/screenshots/homepage.png)](https://adamontherun.github.io/agent-sandboxes/)

This repo is two things: **the book** (16 chapters of prose, nothing to install) and **the code** (runnable examples and failing-test challenges, which need an environment). Every chapter in the book links straight back to Codespaces, so you're never more than one click from a terminal with Python and the AWS CLI already installed.

## What's covered

- **Part I · Foundations** — Why agent sandboxes matter, Firecracker architecture, and Lambda MicroVMs design
- **Part II · Getting Started** — Building your first MicroVM image, launching instances, and lifecycle management
- **Part III · Building an Agent Sandbox** — Code execution, package management, filesystem isolation, and resource limits
- **Part IV · Advanced Patterns** — Multi-tenant isolation, security hardening, observability, and production deployment
- **Part V · Real-World Systems** — AI coding assistant and security testing sandbox patterns

## Setup

Don't want to install anything? Open [the book](https://adamontherun.github.io/agent-sandboxes/) and click "Launch Codespace" in any chapter's sidebar — it opens a cloud dev environment with Python and the AWS CLI already installed.

To run locally, you need [Python 3.11+](https://www.python.org/downloads/) and [the AWS CLI](https://aws.amazon.com/cli/):

```sh
# Install dependencies
pip install -e .

# Configure AWS credentials (requires Lambda MicroVMs access)
aws configure
```

**Note**: Most examples ship an offline simulation path, so you can follow along without an AWS account. Only the examples in Chapters 4–6 make real AWS calls.

## Following along with AWS

The Chapter 4–6 examples run against real AWS Lambda MicroVMs. You don't edit any code — you set your values once in a `.env` file and run the scripts. Here's the whole path, start to finish.

### 1. Install prerequisites

- **Update the AWS CLI to a recent v2.** Lambda MicroVMs commands (`aws lambda-microvms ...`) only exist in newer releases. Check with `aws lambda-microvms help` — if it errors, run `brew upgrade awscli` (or reinstall from [aws.amazon.com/cli](https://aws.amazon.com/cli/)).
- **Configure credentials.** Either run `aws configure --profile microvms` (or `aws configure sso ...` if your org uses IAM Identity Center), then confirm it works:
  ```sh
  aws sts get-caller-identity --profile microvms
  ```

### 2. Create the two AWS prerequisites (one time)

Building a MicroVM image needs an S3 bucket and an IAM build role. Follow the [AWS getting-started guide](https://docs.aws.amazon.com/lambda/latest/dg/microvms-getting-started.html) — you need:

- An **S3 bucket** in your region for the code artifact.
- An **IAM build role** that Lambda can assume (trust policy for `lambda.amazonaws.com`; permissions for `s3:GetObject` on your bucket and `logs:*` for build logs).

### 3. Point the course at your account

```sh
cp .env.example .env
```

Open `.env` and fill in the values (see [`.env.example`](.env.example) for the full annotated list):

| Setting | What it is |
| --- | --- |
| `AWS_PROFILE` | The CLI profile to use (e.g. `microvms`) |
| `AWS_REGION` / `AWS_ACCOUNT_ID` | Your region and 12-digit account ID |
| `MICROVM_BUILD_ROLE_ARN` | The build role from step 2 |
| `MICROVM_EXECUTION_ROLE_ARN` | The IAM role a MicroVM assumes at runtime |
| `MICROVM_IMAGE_ARN` | An image you've built (fill this in after step 4) |
| `MICROVM_INGRESS_PORT` / `MICROVM_REQUEST_PATH` | The port your app listens on (default `8080`) and a route to hit (default `/`) |

The examples load `.env` automatically. Anything already set in your shell environment takes precedence, and `.env` is git-ignored so your values never get committed. (You can also skip `AWS_PROFILE` and put `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` straight in `.env`.)

### 4. Build an image, then launch a MicroVM

```sh
# Build a MicroVM image (uses MICROVM_BUILD_ROLE_ARN). Copy the returned
# image ARN into MICROVM_IMAGE_ARN in your .env.
python examples/ch04_build_image.py

# Launch it, mint an auth token, make an authenticated request, and tear it down.
python examples/ch05_launch_and_connect.py
```

A successful run ends with `Status: 200` and your app's response, then `Terminated.` If you get a **403**, your `MICROVM_INGRESS_PORT` doesn't match the port your app listens on; a **404** means the port is right but `MICROVM_REQUEST_PATH` isn't a route your app serves.

> **Cost:** a running MicroVM bills at a baseline rate. The examples terminate what they launch, but if a run exits early, check for stragglers with `aws lambda-microvms list-microvms --profile <you>` and terminate any that aren't `TERMINATED`.

## Doing challenges

Every chapter has a challenge under `challenges/`: a skeleton file with failing tests. Edit the skeleton until the tests pass:

```sh
pytest challenges/ch04_test.py
```

Reference solutions live in `solutions/`. No peeking until the tests pass.
