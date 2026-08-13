# demo-auth

A tiny fixture project with a known bug: login fails when the email contains
uppercase characters (registration lowercases emails, login does not).

To try SmallCoder on it, first make it a standalone git repo (SmallCoder
requires one for safety):

```bash
cp -r examples/demo-auth /tmp/demo-auth
cd /tmp/demo-auth && git init -q && git add -A && git commit -qm "initial"
```

Then:

```bash
smallcoder solve --repo /tmp/demo-auth \
  --issue "Login fails when the email address contains uppercase characters."
```
