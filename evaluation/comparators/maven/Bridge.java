// Bridge to Maven's ComparableVersion (org.apache.maven:maven-artifact) for
// evaluation baseline V (evaluation/comparators/README.md). Run in source-file
// mode, with no build step:
//   java -cp lib/maven-artifact-3.9.16.jar Bridge.java
// One JSON request per line on stdin, one JSON response per line on stdout;
// the protocol is the npm bridge's.
//
// ComparableVersion accepts every string, so validity here is a rule of the
// baseline, not of Maven: a version is decidable only if its canonical form
// starts with a numeric item (LATEST, RELEASE and ${...} placeholders are not).
// The release core is the numeric items before the first sub-list ('-').

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import org.apache.maven.artifact.versioning.ComparableVersion;

public class Bridge {
    static final String POM =
            "/META-INF/maven/org.apache.maven/maven-artifact/pom.properties";

    static String libraryVersion() {
        try (InputStream in = ComparableVersion.class.getResourceAsStream(POM)) {
            if (in == null) {
                return "";
            }
            Properties p = new Properties();
            p.load(in);
            return p.getProperty("version", "");
        } catch (Exception e) {
            return "";
        }
    }

    static boolean digits(String s) {
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            if (!Character.isDigit(s.charAt(i))) {
                return false;
            }
        }
        return true;
    }

    static String parse(String v) {
        if (v == null || v.trim().isEmpty()) {
            return "\"valid\":false";
        }
        String canonical = new ComparableVersion(v).getCanonical();
        int dash = canonical.indexOf('-');
        String release = dash >= 0 ? canonical.substring(0, dash) : canonical;
        List<String> core = new ArrayList<>();
        for (String part : release.split("\\.", -1)) {
            if (!digits(part)) {
                break;
            }
            core.add(part);
        }
        if (core.isEmpty()) {
            return "\"valid\":false,\"canonical\":" + quote(canonical);
        }
        boolean qualified = dash >= 0 || core.size() < release.split("\\.", -1).length;
        return "\"valid\":true,\"core\":[" + String.join(",", core) + "],\"prerelease\":"
                + qualified + ",\"canonical\":" + quote(canonical);
    }

    static String handle(Map<String, String> req) {
        String op = req.getOrDefault("op", "");
        switch (op) {
            case "version":
                return "\"library\":\"org.apache.maven:maven-artifact\",\"version\":"
                        + quote(libraryVersion());
            case "parse":
                return parse(req.get("v"));
            case "compare": {
                String a = req.get("a");
                String b = req.get("b");
                if (a == null || b == null || !parse(a).startsWith("\"valid\":true")
                        || !parse(b).startsWith("\"valid\":true")) {
                    return "\"cmp\":null";
                }
                int c = new ComparableVersion(a).compareTo(new ComparableVersion(b));
                return "\"cmp\":" + Integer.signum(c);
            }
            default:
                return "\"error\":" + quote("unknown op " + op);
        }
    }

    // --- a minimal reader for the flat requests the adapter sends ----------

    static Map<String, String> read(String line) {
        Map<String, String> out = new HashMap<>();
        int i = skip(line, 0);
        if (i >= line.length() || line.charAt(i) != '{') {
            throw new IllegalArgumentException("not an object");
        }
        i = skip(line, i + 1);
        while (i < line.length() && line.charAt(i) != '}') {
            StringBuilder key = new StringBuilder();
            i = string(line, i, key);
            i = skip(line, i);
            if (line.charAt(i) != ':') {
                throw new IllegalArgumentException("expected ':'");
            }
            i = skip(line, i + 1);
            StringBuilder value = new StringBuilder();
            if (line.charAt(i) == '"') {
                i = string(line, i, value);
            } else {
                while (i < line.length() && ",} \t".indexOf(line.charAt(i)) < 0) {
                    value.append(line.charAt(i++));
                }
            }
            out.put(key.toString(), value.toString());
            i = skip(line, i);
            if (i < line.length() && line.charAt(i) == ',') {
                i = skip(line, i + 1);
            }
        }
        return out;
    }

    static int skip(String s, int i) {
        while (i < s.length() && Character.isWhitespace(s.charAt(i))) {
            i++;
        }
        return i;
    }

    static int string(String s, int i, StringBuilder out) {
        if (s.charAt(i) != '"') {
            throw new IllegalArgumentException("expected a string");
        }
        i++;
        while (s.charAt(i) != '"') {
            char c = s.charAt(i++);
            if (c == '\\') {
                char e = s.charAt(i++);
                switch (e) {
                    case 'n': out.append('\n'); break;
                    case 't': out.append('\t'); break;
                    case 'r': out.append('\r'); break;
                    case 'b': out.append('\b'); break;
                    case 'f': out.append('\f'); break;
                    case 'u':
                        out.append((char) Integer.parseInt(s.substring(i, i + 4), 16));
                        i += 4;
                        break;
                    default: out.append(e);
                }
            } else {
                out.append(c);
            }
        }
        return i + 1;
    }

    static String quote(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            if (c == '"' || c == '\\') {
                b.append('\\').append(c);
            } else if (c < 0x20) {
                b.append(String.format("\\u%04x", (int) c));
            } else {
                b.append(c);
            }
        }
        return b.append('"').toString();
    }

    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = in.readLine()) != null) {
            String body;
            String id = "null";
            try {
                Map<String, String> req = read(line);
                id = req.getOrDefault("id", "null");
                if (!id.matches("-?\\d+")) {
                    id = "null";
                }
                body = handle(req);
            } catch (Exception e) {
                body = "\"error\":\"bad request\"";
            }
            System.out.println("{\"id\":" + id + "," + body + "}");
            System.out.flush();
        }
    }
}
