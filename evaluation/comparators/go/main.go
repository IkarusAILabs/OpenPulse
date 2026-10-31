// Bridge to golang.org/x/mod/semver for evaluation baseline V
// (evaluation/comparators/README.md). One JSON request per line on stdin,
// one JSON response per line on stdout; the protocol is the npm bridge's.
// Versions are taken as given: Go's semver requires the "v" prefix, and the
// Python adapter adds it for OSV-style inputs that omit it.
package main

import (
	"bufio"
	"encoding/json"
	"os"
	"runtime/debug"
	"strconv"
	"strings"

	"golang.org/x/mod/semver"
)

type request struct {
	ID int    `json:"id"`
	Op string `json:"op"`
	V  string `json:"v"`
	A  string `json:"a"`
	B  string `json:"b"`
}

func libraryVersion() string {
	info, ok := debug.ReadBuildInfo()
	if !ok {
		return ""
	}
	for _, dep := range info.Deps {
		if dep.Path == "golang.org/x/mod" {
			return dep.Version
		}
	}
	return ""
}

func parse(v string) map[string]any {
	if !semver.IsValid(v) {
		return map[string]any{"valid": false}
	}
	canonical := semver.Canonical(v)
	release := strings.TrimPrefix(canonical, "v")
	if i := strings.IndexByte(release, '-'); i >= 0 {
		release = release[:i]
	}
	core := []int64{}
	for _, part := range strings.Split(release, ".") {
		n, err := strconv.ParseInt(part, 10, 64)
		if err != nil {
			return map[string]any{"valid": false}
		}
		core = append(core, n)
	}
	return map[string]any{
		"valid":      true,
		"core":       core,
		"prerelease": semver.Prerelease(v) != "",
		"canonical":  canonical,
	}
}

func handle(req request) map[string]any {
	switch req.Op {
	case "version":
		return map[string]any{"library": "golang.org/x/mod", "version": libraryVersion()}
	case "parse":
		return parse(req.V)
	case "compare":
		if !semver.IsValid(req.A) || !semver.IsValid(req.B) {
			return map[string]any{"cmp": nil}
		}
		return map[string]any{"cmp": semver.Compare(req.A, req.B)}
	default:
		return map[string]any{"error": "unknown op " + req.Op}
	}
}

func main() {
	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	out := json.NewEncoder(os.Stdout)
	for in.Scan() {
		var req request
		if err := json.Unmarshal(in.Bytes(), &req); err != nil {
			_ = out.Encode(map[string]any{"error": "bad request"})
			continue
		}
		resp := handle(req)
		resp["id"] = req.ID
		if err := out.Encode(resp); err != nil {
			os.Exit(1)
		}
	}
}
