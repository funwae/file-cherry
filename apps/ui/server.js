#!/usr/bin/env node

/**
 * Simple Next.js server entry point for FileCherry UI.
 *
 * This can be used as the ExecStart command in systemd:
 * /opt/filecherry/apps/ui/node_modules/.bin/next start -p 3000
 *
 * Or run directly:
 * node server.js
 */

const { createServer } = require('http')
const next = require('next')

const dev = process.env.NODE_ENV !== 'production'
const hostname = process.env.HOST || '0.0.0.0'
const port = parseInt(process.env.PORT || '3000', 10)

const app = next({ dev, hostname, port })
const handle = app.getRequestHandler()

app.prepare().then(() => {
  createServer((req, res) => {
    handle(req, res)
  }).listen(port, hostname, (err) => {
    if (err) throw err
    console.log(`> Ready on http://${hostname}:${port}`)
  })
})

