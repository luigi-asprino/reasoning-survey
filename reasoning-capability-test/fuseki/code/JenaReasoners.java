// Runs the Jena reasoners that Fuseki can use directly through the Jena API,
// to get what the SPARQL endpoint does not expose:
//   - preparation time (the analogue of GraphDB's materialisation at load time),
//   - number of implicit triples, per predicate (the analogue of onto:implicit),
//   - consistency checking via InfModel.validate().
//
// No build needed: Java 17+ runs the source file directly, with the Fuseki jar
// (which bundles Jena) on the classpath:
//
//   java -cp <fuseki-dir>/fuseki-server.jar JenaReasoners.java ../../graphdb/data/university.ttl
//   java -cp <fuseki-dir>/fuseki-server.jar JenaReasoners.java --reasoners rdfs,owl ../../graphdb/data/university.ttl
//   java -cp <fuseki-dir>/fuseki-server.jar JenaReasoners.java --validate-only ../../graphdb/data/inconsistent.ttl
//   java -cp <fuseki-dir>/fuseki-server.jar JenaReasoners.java --top 0 onto.ttl data.ttl   (all predicates)
//
// Output is Markdown on stdout; redirect it to ../results/.

import org.apache.jena.rdf.model.*;
import org.apache.jena.reasoner.Reasoner;
import org.apache.jena.reasoner.ReasonerRegistry;
import org.apache.jena.reasoner.ValidityReport;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.shared.PrefixMapping;

import java.util.*;

public class JenaReasoners {

    static final LinkedHashMap<String, java.util.function.Supplier<Reasoner>> REASONERS = new LinkedHashMap<>();
    static {
        REASONERS.put("transitive", ReasonerRegistry::getTransitiveReasoner);
        REASONERS.put("rdfs", ReasonerRegistry::getRDFSReasoner);
        REASONERS.put("owl-micro", ReasonerRegistry::getOWLMicroReasoner);
        REASONERS.put("owl-mini", ReasonerRegistry::getOWLMiniReasoner);
        REASONERS.put("owl", ReasonerRegistry::getOWLReasoner);
    }

    public static void main(String[] args) {
        List<String> names = new ArrayList<>(REASONERS.keySet());
        List<String> files = new ArrayList<>();
        boolean validateOnly = false;
        int top = 15;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--reasoners" -> names = Arrays.asList(args[++i].split(","));
                case "--validate-only" -> validateOnly = true;
                case "--top" -> top = Integer.parseInt(args[++i]);
                default -> files.add(args[i]);
            }
        }
        if (files.isEmpty()) {
            System.err.println("usage: JenaReasoners [--reasoners a,b] [--validate-only] [--top N] file...");
            System.exit(1);
        }

        Model base = ModelFactory.createDefaultModel();
        for (String f : files) RDFDataMgr.read(base, f);
        PrefixMapping pm = base;

        System.out.println("# Jena reasoners report\n");
        System.out.println("Data: " + String.join(", ", files) + " · explicit triples: " + base.size() + "\n");
        System.out.println("| Reasoner | Prepare (ms) | Total triples | Implicit triples | Consistent | Validate (ms) |");
        System.out.println("|---|---|---|---|---|---|");

        Map<String, Map<String, Integer>> perPredicate = new LinkedHashMap<>();
        Map<String, List<String>> reports = new LinkedHashMap<>();

        for (String name : names) {
            var sup = REASONERS.get(name);
            if (sup == null) { System.err.println("unknown reasoner " + name + "; known: " + REASONERS.keySet()); continue; }
            InfModel inf = ModelFactory.createInfModel(sup.get(), base);

            long t0 = System.nanoTime();
            inf.prepare();
            long prepMs = (System.nanoTime() - t0) / 1_000_000;

            long total = -1, implicit = -1;
            if (!validateOnly) {
                Map<String, Integer> counts = new TreeMap<>();
                total = 0; implicit = 0;
                StmtIterator it = inf.listStatements();
                while (it.hasNext()) {
                    Statement s = it.next();
                    total++;
                    if (!base.contains(s)) {
                        implicit++;
                        counts.merge(pm.shortForm(s.getPredicate().getURI()), 1, Integer::sum);
                    }
                }
                perPredicate.put(name, counts);
            }

            String consistent = "n/a";
            long valMs = 0;
            if (!name.equals("transitive")) {   // the transitive reasoner has no validation rules
                t0 = System.nanoTime();
                ValidityReport vr = inf.validate();
                valMs = (System.nanoTime() - t0) / 1_000_000;
                consistent = vr.isValid() ? (vr.isClean() ? "yes" : "yes (warnings)") : "**no**";
                List<String> lines = new ArrayList<>();
                vr.getReports().forEachRemaining(r ->
                        lines.add((r.isError() ? "ERROR " : "warning ") + r.getType() + ": " + r.getDescription().replace('\n', ' ')));
                reports.put(name, lines);
            }
            System.out.printf("| %s | %d | %s | %s | %s | %d |%n", name, prepMs,
                    total < 0 ? "–" : total, implicit < 0 ? "–" : implicit, consistent, valMs);
        }

        if (!perPredicate.isEmpty()) {
            System.out.println("\n## Implicit triples per predicate\n");
            Set<String> preds = new TreeSet<>();
            perPredicate.values().forEach(m -> preds.addAll(m.keySet()));
            List<String> rows = new ArrayList<>(preds);
            rows.sort(Comparator.comparingInt((String p) ->
                    -perPredicate.values().stream().mapToInt(m -> m.getOrDefault(p, 0)).max().orElse(0)));
            if (top > 0 && rows.size() > top) rows = rows.subList(0, top);
            System.out.println("| Predicate | " + String.join(" | ", perPredicate.keySet()) + " |");
            System.out.println("|---|" + "---|".repeat(perPredicate.size()));
            for (String p : rows) {
                StringBuilder sb = new StringBuilder("| " + p + " |");
                for (var m : perPredicate.values()) sb.append(" ").append(m.getOrDefault(p, 0)).append(" |");
                System.out.println(sb);
            }
            if (top > 0 && preds.size() > top)
                System.out.println("\n(top " + top + " of " + preds.size() + " predicates; use --top 0 for all)");
        }

        System.out.println("\n## Validation reports\n");
        reports.forEach((name, lines) -> {
            System.out.println("### " + name + "\n");
            if (lines.isEmpty()) System.out.println("No reports.\n");
            else { lines.forEach(l -> System.out.println("- " + l)); System.out.println(); }
        });
    }
}
