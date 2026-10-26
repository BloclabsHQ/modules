# Stable SNS Lambda packages — durable spec

**Tracking issue:** https://github.com/BloclabsHQ/modules/issues/73

**Goal (issue brief):** See issue § Goal.
**Done when (acceptance):** See issue § Done when.
**Out of scope (issue brief):** See issue § Out of scope.

## 1. Systems touched

**Top-down:** The account drift review reaches `BloclabsHQ/iac`'s DEV SNS
forwarder and this repository's `modules/sns/slack/main.tf`. Package selection
currently includes a generated Terragrunt source manifest. Restrict selection
to the existing `functions/app.py`; preserve the handler and all runtime,
permission, environment, destination and resource interfaces.

**Bottom-up:** Add regression coverage under `modules/sns/tests/` using the
actual pinned `terraform-aws-modules/lambda/aws` 6.4.0 package builder. The
consuming account repository adopts the merged revision in `modules.commit`
and the outer BlocLabs workspace adopts the same `modules` gitlink. Its DEV
and PROD SNS declarations share this module, but only a newly reviewed DEV
plan is in the operational continuation. No workflow or approval-control
source changes belong here.

## 2. Security

**Auth:** Existing repository contribution and consumer saved-plan controls.
**Operator/admin routes:** No new route; the account operator uses the existing
[plan/apply procedure](https://github.com/BloclabsHQ/iac/blob/main/docs/terraform-plan-handoff.md)
and [operator authorization](https://github.com/BloclabsHQ/fabricbloc/blob/main/architecture/canonical-contracts/operator-authorization.md).
**Secrets:** No new secrets or secret changes. The existing webhook remains
with the [account notification-secret owner](https://github.com/BloclabsHQ/iac/blob/main/docs/aws-account-operating-model.md#notification-secrets).
Tests use source files and synthetic cache metadata, with no credentials or AWS.

## 3. Policy

**New decision:** none. Exact-plan authorization and native apply controls stay
with the consumer. Source merge is not deployment evidence.

## 4. Cost

**Cost class:** Existing infrastructure; no new AWS resources or CI workflow.
**Cost review:** no — package input correction adds no standing resource,
schedule, paid dependency or workload capacity.

## 5. Data

Application source and synthetic generated-file fixtures only. Tests use
temporary local directories and delete them on exit. Never save a decoded
Terraform plan, webhook or live configuration values as a review artifact.

## 6. Infra

Consumer `BloclabsHQ/iac`, account `899575023171`, region `us-west-2`, unit
`dev/sns`, existing function `mgb-dev-sns-slack`. No apply is performed from
this module repository. No network, IAM or destination configuration changes.

## 7. Rollout and rollback

**Rollout:** Pass the independent spec gate; implement the file selection and
regression tests; independently review and merge this module change. Then
adopt that immutable revision through the account and outer workspace PRs.
Generate a fresh native DEV SNS plan from clean merged sources. Review all
package/version/permission actions, resolve its exact authorization, apply
once, and verify archive contents, unchanged environment, Lambda status and
existing subscription/permission scope. Preserve application-delivery proof
as a separate observation. No prod secret or custody change; no PROD apply.

**Revert trigger:** Missing handler, non-source package entries, lost code
change detection, or changed runtime/permission/environment scope blocks
publication. If post-deployment verification fails, the account owner prepares
a fresh exact recovery plan using known-good handler/configuration; do not
edit state, replay an old plan or infer rollback from reverting source.

## 8. Links

- https://github.com/BloclabsHQ/modules/issues/73
- https://github.com/BloclabsHQ/iac/issues/244
- https://github.com/BloclabsHQ/fabric-iac/issues/1100

## 9. Behavior and interfaces

B1: Change only the existing source-path object's `path` from the directory to
`${path.module}/functions/app.py`. Execute the pinned builder in separate
fixture working directories with identical handler bytes, mode 0644 and mtime
1577836800. Use the same relative `slack/functions/app.py` path beneath each
fixture cwd; vary only `.terragrunt-source-manifest` contents. Normalize only
fixture metadata, not production packaging. Assert the same content-derived
filename and ZIP bytes, and exactly one archive member named `app.py`.

B2: Alter handler bytes in a third fixture and assert a different package
identity and archive bytes. This tests the real builder, not a reimplemented
hash or a string-only expectation.

B3: Existing handler/HTTP-boundary tests remain passing; check Terraform
formatting and whitespace. Implement `modules/sns/tests/test_package.py`; run
`SNS_LAMBDA_PACKAGE_SCRIPT=/absolute/path/to/lambda-6.4.0/package.py python3 -m unittest discover -s modules/sns/tests -p test_package.py`.
The required environment variable supplies the installed builder. Verify its
SHA-256 is `9ad2f39ce95cddb5c6460d8eeab543c5e3ab1c858910556f4e3a5f76910948b8`;
fail when absent or mismatched instead of silently skipping. The fixture reads
the source-path expression from the module so restoring directory selection
reproduces the original defect.

B4: Publish the exact module merge and its test evidence on the tracking issue;
record adoption and subsequent plan/apply evidence separately in iac#244.
