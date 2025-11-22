# Security and Privacy Considerations

## Threat Model

- Primary risk: data exposure from sensitive `inputs/` and `outputs/`.
- Secondary risk: compromised USB might run malicious code on a host if mounted.
- Tertiary risk: misuse of network connectivity or leaked tokens (future GitHub integration).

## Principles

1. **Local by Default**
   - All processing is local unless explicitly configured otherwise.
   - No automatic external API calls in baseline configuration.

2. **No Background Network Access**
   - On initial versions, networking can be disabled entirely or limited.
   - Optional "online mode" must be opt-in and clearly indicated.

3. **Data Isolation**

- OS interacts only with files within `/data`.
- No automatic crawling of other host disks when installed locally.
- When used as live USB, it does not mount host drives without explicit user action.

4. **Permission Model**

- Data partition:
  - owned by a dedicated user (e.g. `filecherry`).
  - services run under this user.
- No `sudo` for UI-level operations.
- Critical system files are read-only.

5. **GitHub / Cloud Tokens (Future)**

- Stored in `config/secrets.yaml` with clear documentation.
- Only used by specific services (e.g. GitHub uploader).
- Option to encrypt secrets with a passphrase requested at boot.

6. **Logging Policy**

- Logs are restricted to operational data:
  - file paths
  - error codes
  - high-level job descriptions.
- Content snippets only logged when explicitly enabled for debugging.
- Provide a "scrub logs" command to delete all logs.

7. **USB Use on Host Machines**

- Data partition is plain exFAT/ext4.
- No autorun scripts for Mac/Windows (to avoid OS-level security issues).
- Ship guidance: "Treat this USB as sensitive; do not leave it in public machines."

8. **Physical Security**

- Encourage users to:
  - label the stick ("Contains sensitive business data").
  - keep in locked drawers when not in use.

9. **Updates and Supply Chain**

- All OS images should be:
  - signed
  - downloadable from a known location.
- Provide checksum verification instructions.

