# Official Sources

Checked 2026-11-02. Reopen the applicable documentation before deployment; the
CLI and Dashboard evolve independently.

- Cloudflare CLI overview: https://developers.cloudflare.com/cf/
  - `cf` commands, typed `cloudflare.config.ts`, and how `cf` relates to Wrangler.
- Cloudflare CLI sign-in and account selection: https://developers.cloudflare.com/cf/get-started/
  - `cf auth login`, `cf auth whoami`, credential/profile precedence, account
    selection precedence, `--profile`, and `.env` loading for deploy commands.
    `CLOUDFLARE_API_TOKEN` from the process environment or `.env` takes
    precedence over saved profiles; process variables override matching `.env`
    values. `cf deploy` and `cf workers triggers deploy` read `.env` after build.
- Cloudflare CLI environment variables: https://developers.cloudflare.com/cf/environment-variables/
  - Credential override behavior and supported `cf` process environment.
    `CLOUDFLARE_ACCOUNT_ID` overrides the `accountId` project setting.
- `cf` typed project configuration: https://developers.cloudflare.com/cf/projects/cloudflare-config/
  - `accountId`, mode-dependent configuration evaluation, Worker naming, and
    mode defaults for `cf deploy` versus Wrangler/API commands.
- Guidance for coding agents: https://developers.cloudflare.com/cf/agents/
  - Existing Wrangler projects keep Wrangler; command discovery uses
    `cf cli search`, then `cf schema` or `--help`.
- `cf` project setup, build, and deploy: https://developers.cloudflare.com/cf/projects/
  - Automatic configuration behavior and `cf` build-script caveats.
- Cloudflare CLI in CI: https://developers.cloudflare.com/cf/ci/
  - Non-interactive authentication, repository secrets, and project setup.
- Dashboard getting started: https://developers.cloudflare.com/workers/get-started/dashboard/
  - Create and deploy a Worker through Workers & Pages.
- Cloudflare Pages getting started: https://developers.cloudflare.com/pages/get-started/
  - Pages project deployment paths. Follow Pages guidance rather than Worker commands.
- Wrangler Pages commands: https://developers.cloudflare.com/workers/wrangler/commands/pages/
  - Current Wrangler Pages-specific local development and deployment commands.
- Wrangler: https://developers.cloudflare.com/workers/wrangler/
  - Wrangler project configuration and commands.
- Wrangler general commands: https://developers.cloudflare.com/workers/wrangler/commands/general/
  - `--config`, `--env`, `--env-file`, and `--profile` flags; `--env-file`
    ordering; `wrangler login`; `wrangler whoami --account` membership checks;
    and credential handling. Do not run `wrangler auth token` during
    credential inspection because it prints token material.
- Wrangler system environment variables:
  https://developers.cloudflare.com/workers/wrangler/system-environment-variables/
  - Wrangler system-variable sources, supported Cloudflare account/auth
    variables, `.env.<environment>` selection, and `CLOUDFLARE_ENV`.
- Wrangler authentication profiles:
  https://developers.cloudflare.com/workers/wrangler/profiles/
  - Profile resolution order, `CLOUDFLARE_API_TOKEN` overriding profiles,
    directory-bound profiles, and target account selection.
- Wrangler account resolver source:
  https://github.com/cloudflare/workers-sdk/blob/main/packages/wrangler/src/user/user.ts
  - Current implementation order for `config.account_id`,
    `CLOUDFLARE_ACCOUNT_ID`, and cached account selection. Recheck against the
    exact installed Wrangler version because the `main` branch can change.
- Wrangler configuration: https://developers.cloudflare.com/workers/wrangler/configuration/
  - `account_id`, Worker configuration, and environment-specific settings.
- List Worker Scripts API: https://developers.cloudflare.com/api/resources/workers/subresources/scripts/methods/list/
  - Read-only listing of uploaded Worker scripts for a specified account.
- Cron Triggers: https://developers.cloudflare.com/workers/configuration/cron-triggers/
  - `scheduled()` handler, UTC schedules, project configuration, local tests,
    propagation, Cron Events, and trigger removal behavior.
- Local Explorer: https://developers.cloudflare.com/workers/local-development/local-explorer/
  - Local invocation and current tool-version requirements.
- Scheduled handler: https://developers.cloudflare.com/workers/runtime-apis/handlers/scheduled/
  - Local scheduled route and handler behavior.
- Worker logs: https://developers.cloudflare.com/workers/observability/logs/
  - Available logging and investigation surfaces.
- Real-time logs: https://developers.cloudflare.com/workers/observability/logs/real-time-logs/
  - Dashboard live logs, sampling, and availability notes.
- Secrets: https://developers.cloudflare.com/workers/configuration/secrets/
  - Encrypted secret bindings and safe secret management.
- Versions and deployments: https://developers.cloudflare.com/workers/versions-and-deployments/
  - Version/deployment model and the separation between code versions and
    stateful resource changes.
- Rollbacks: https://developers.cloudflare.com/workers/versions-and-deployments/rollbacks/
  - Rollback behavior and resource/data caveats.
- Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
  - Review current plan and usage costs when a task could incur charges.
