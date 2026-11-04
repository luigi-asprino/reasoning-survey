// Loading-time benchmark for one Jena reasoner (the engine behind Fuseki's
// ja:InfModel datasets). Driven by benchmark_reasoners.py, which runs one JVM
// per reasoner so that a timeout or an out-of-memory error stops only that
// reasoner.
//
// For every run (warm-up runs first):
//   1. parse the ontology files into a fresh in-memory model (timed);
//   2. parse the data files into the same model (timed);
//   3. wrap it in an InfModel and call prepare() (timed): forward rules fire here;
//   4. list every statement of the InfModel (timed): this forces the backward
//      rules too, so steps 3 + 4 compute the full closure, the analogue of
//      GraphDB's materialisation on commit;
//   5. optionally run validate() (timed): the consistency check;
// and print one JSON line with the timings and the explicit / inferred counts.
//
// Usage (Java 17+, Fuseki jar on the classpath, no build needed):
//   java -cp fuseki-server.jar JenaLoadBench.java --reasoner owl-mini --runs 3 --warmup 1 \
//        [--validate] --onto a.ttl b.owl --data c.ttl
//
// Reasoners: none, transitive, rdfs, owl-micro, owl-mini, owl, and compiled
// (a rule profile from jena-rule-profile/code/compile_rules.py, given with --rules FILE;
// its consistency checks are counted from the urn:jena-profile#violates triples).

import org.apache.jena.graph.Graph;
import org.apache.jena.graph.Triple;
import org.apache.jena.rdf.model.*;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.reasoner.ReasonerRegistry;
import org.apache.jena.reasoner.ValidityReport;
import org.apache.jena.reasoner.rulesys.GenericRuleReasoner;
import org.apache.jena.reasoner.rulesys.Rule;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.riot.RDFLanguages;
import org.apache.jena.riot.RiotException;
import org.apache.jena.util.iterator.ExtendedIterator;

import java.util.*;

public class JenaLoadBench {

    static String rulesFile = null;

    static Reasoner reasoner(String name) {
        return switch (name) {
            case "compiled" -> {
                if (rulesFile == null) throw new IllegalArgumentException("--rules FILE is required for 'compiled'");
                // forward rules only, run by the RETE engine: inferences are materialised in prepare()
                GenericRuleReasoner r = new GenericRuleReasoner(Rule.rulesFromURL(rulesFile));
                r.setMode(GenericRuleReasoner.FORWARD_RETE);
                yield r;
            }
            case "none" -> null;
            case "transitive" -> ReasonerRegistry.getTransitiveReasoner();
            case "rdfs" -> ReasonerRegistry.getRDFSReasoner();
            case "owl-micro" -> ReasonerRegistry.getOWLMicroReasoner();
            case "owl-mini" -> ReasonerRegistry.getOWLMiniReasoner();
            case "owl" -> ReasonerRegistry.getOWLReasoner();
            default -> throw new IllegalArgumentException("unknown reasoner " + name);
        };
    }

    /** Parse a file; a .owl/.rdf/.xml file that is not RDF/XML is retried as Turtle (DUL.owl is Turtle). */
    static void read(Model target, String file) {
        Model tmp = ModelFactory.createDefaultModel();
        try {
            RDFDataMgr.read(tmp, file);
        } catch (RiotException e) {
            Lang guessed = RDFLanguages.filenameToLang(file);
            if (guessed != Lang.RDFXML) throw e;
            tmp = ModelFactory.createDefaultModel();
            RDFDataMgr.read(tmp, file, Lang.TURTLE);
        }
        target.add(tmp);
    }

    static double secs(long t0) { return (System.nanoTime() - t0) / 1e9; }

    static String json(Map<String, Object> m) {
        StringBuilder sb = new StringBuilder("{");
        for (var e : m.entrySet()) {
            if (sb.length() > 1) sb.append(',');
            sb.append('"').append(e.getKey()).append("\":");
            Object v = e.getValue();
            if (v == null) sb.append("null");
            else if (v instanceof Number || v instanceof Boolean) sb.append(v);
            else sb.append('"').append(v.toString().replace("\\", "\\\\").replace("\"", "\\\"")
                        .replace("\n", " ").replace("\r", " ")).append('"');
        }
        return sb.append('}').toString();
    }

    public static void main(String[] args) {
        String name = null;
        int runs = 3, warmup = 1;
        boolean validate = false;
        List<String> onto = new ArrayList<>(), data = new ArrayList<>();
        List<String> cur = null;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--reasoner" -> { name = args[++i]; cur = null; }
                case "--runs" -> { runs = Integer.parseInt(args[++i]); cur = null; }
                case "--warmup" -> { warmup = Integer.parseInt(args[++i]); cur = null; }
                case "--validate" -> { validate = true; cur = null; }
                case "--rules" -> { rulesFile = args[++i]; cur = null; }
                case "--onto" -> cur = onto;
                case "--data" -> cur = data;
                default -> {
                    if (cur == null) throw new IllegalArgumentException("unexpected argument " + args[i]);
                    cur.add(args[i]);
                }
            }
        }
        if (name == null) throw new IllegalArgumentException("--reasoner is required");

        for (int run = 1; run <= warmup + runs; run++) {
            Map<String, Object> r = new LinkedHashMap<>();
            r.put("reasoner", name);
            r.put("run", run);
            r.put("warmup", run <= warmup);
            try {
                Model base = ModelFactory.createDefaultModel();
                long t0 = System.nanoTime();
                for (String f : onto) read(base, f);
                r.put("onto_load_s", secs(t0));
                t0 = System.nanoTime();
                for (String f : data) read(base, f);
                r.put("data_load_s", secs(t0));
                long explicit = base.size();
                r.put("explicit", explicit);

                Reasoner reasoner = reasoner(name);
                if (reasoner == null) {
                    r.put("prepare_s", 0.0);
                    r.put("closure_s", 0.0);
                    r.put("inferred", 0L);
                    r.put("total", explicit);
                } else {
                    InfModel inf = ModelFactory.createInfModel(reasoner, base);
                    t0 = System.nanoTime();
                    inf.prepare();
                    r.put("prepare_s", secs(t0));

                    t0 = System.nanoTime();
                    Graph g = inf.getGraph(), bg = base.getGraph();
                    long total = 0, inferred = 0;
                    ExtendedIterator<Triple> it = g.find();
                    while (it.hasNext()) {
                        Triple t = it.next();
                        total++;
                        if (!bg.contains(t)) inferred++;
                    }
                    r.put("closure_s", secs(t0));
                    r.put("inferred", inferred);
                    r.put("total", total);

                    if (validate && name.equals("compiled")) {
                        t0 = System.nanoTime();
                        Property violates = inf.createProperty("urn:jena-profile#violates");
                        List<String> errs = new ArrayList<>();
                        long n = 0;
                        for (StmtIterator vi = inf.listStatements(null, violates, (RDFNode) null); vi.hasNext(); ) {
                            Statement st = vi.next();
                            n++;
                            if (errs.size() < 3) errs.add(st.getSubject() + ": " + st.getObject());
                        }
                        r.put("validate_s", secs(t0));
                        r.put("consistent", n == 0);
                        if (n > 0) r.put("error", n + " violation(s); " + String.join(" | ", errs));
                    } else if (validate && !name.equals("transitive")) {
                        t0 = System.nanoTime();
                        ValidityReport vr = inf.validate();
                        r.put("validate_s", secs(t0));
                        r.put("consistent", vr.isValid());
                        if (!vr.isValid()) {
                            List<String> errs = new ArrayList<>();
                            int n = 0;
                            for (var it2 = vr.getReports(); it2.hasNext(); ) {
                                ValidityReport.Report rep = it2.next();
                                if (!rep.isError()) continue;
                                n++;
                                if (errs.size() < 3) errs.add(rep.getType() + ": " + rep.getDescription());
                            }
                            r.put("error", n + " error(s); " + String.join(" | ", errs));
                        }
                    }
                }
            } catch (OutOfMemoryError e) {
                r.put("error", "OutOfMemoryError (raise --xmx)");
                System.out.println(json(r));
                System.out.flush();
                System.exit(3);
            } catch (Exception e) {
                r.put("error", e.getClass().getSimpleName() + ": " + e.getMessage());
            }
            System.out.println(json(r));
            System.out.flush();
            System.gc();
        }
    }
}
