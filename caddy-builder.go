package main

import (
	caddycmd "github.com/caddyserver/caddy/v2/cmd"

	// Core Caddy modules
	_ "github.com/caddyserver/caddy/v2/modules/standard"

	// Essential plugins for development
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/reverseproxy"
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/fileserver"
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/templates"
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/encode"
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/headers"
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/rewrite"

	// Authentication
	_ "github.com/caddyserver/caddy/v2/modules/caddyhttp/caddyauth"

	// Useful third-party plugins
	// Commented out due to invalid version issues in dependencies
	// _ "github.com/caddy-dns/cloudflare"
	// _ "github.com/greenpau/caddy-security"
	// _ "github.com/hslatman/caddy-crowdsec-bouncer"
	// _ "github.com/mholt/caddy-ratelimit"
	// _ "github.com/porech/caddy-maxmind-geolocation"
	
	// Development and debugging plugins
	// Commented out due to invalid version issues in dependencies
	// _ "github.com/caddyserver/transform-encoder"
	// _ "github.com/caddy-dns/route53"
	
	// API and WebSocket support
	// Commented out due to invalid version issues in dependencies
	// _ "github.com/mholt/caddy-webdav"
	// _ "github.com/abiosoft/caddy-exec"
	
	// Logging and monitoring
	_ "github.com/caddyserver/caddy/v2/modules/logging"
	
	// Cache plugins
	// Commented out due to invalid version issues in dependencies
	// _ "github.com/sillygod/cdp-cache"
	
	// Metrics and observability
	// Commented out due to invalid version issues in dependencies
	// _ "github.com/hairyhenderson/caddy-teapot-module"
)

func main() {
	caddycmd.Main()
}
