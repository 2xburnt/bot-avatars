# bot-avatars

Public avatar images the Slack gateways send as `icon_url` for each bot profile, plus the
`slack-identity` Hermes plugin that attaches them.

Public by necessity: Slack fetches `icon_url` anonymously.

- `<profile>.png`: avatar for that profile (burntkeeper, burntscout, burntsentry, burntdev, burntlibrarian).
- `slack-identity/`: Hermes plugin. Copy to `<HERMES_HOME>/plugins/slack-identity`, then
  `hermes plugins enable slack-identity`. Needs the Slack app scope `chat:write.customize`.
  Config:

      plugins:
        entries:
          slack-identity:
            settings:
              profiles:
                <profile>: {username: <Display Name>, icon_url: https://raw.githubusercontent.com/2xburnt/bot-avatars/main/<profile>.png}

  A post into a channel that an enabled slack entry of `gateway.profile_routes` maps to a listed
  profile gets that profile's name and avatar. Posts that set their own username/icon, and every
  other channel, are untouched.
