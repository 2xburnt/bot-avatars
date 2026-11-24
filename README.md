# bot-avatars

Public avatar images the Slack gateways send as `icon_url` for each bot profile, plus the
`slack-identity` Hermes plugin that attaches them.

Public by necessity: Slack fetches `icon_url` anonymously.

- `<profile>.png`: 512px avatar for that profile (burntbot, burntsentry, burntscout, burntkeeper, burntdev,
  burntlibrarian, crucible). One family: the black armored robot on the orange lava backdrop, one robot color per bot
  (sentry red, scout green, keeper blue, dev yellow, librarian purple; burntbot keeps the original orange).
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
