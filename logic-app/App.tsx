// ==============================
// App.tsx
//
// This is the single-screen UI for your app.
// It:
//  1) Lets user enter ONE formula -> generate truth table + truth tree
//  2) Lets user enter premises (1-3) + conclusion -> generate argument truth tree
// ==============================

import React, { useMemo, useState } from "react";
import {
  SafeAreaView,
  Text,
  TextInput,
  Button,
  ScrollView,
  View,
} from "react-native";

// These functions are wrappers around axios calls to your FastAPI backend
import { getTruthTable, getTruthTree, getArgumentTree } from "./src/api";

// ------------------------------
// Type for /truth-table response
// ------------------------------
type TruthTableResponse = {
  variables: string[];
  rows: Array<{
    assignment: Record<string, boolean>;
    value: boolean;
  }>;
  error?: string;
};

export default function App() {
  // ==========================================================
  // SECTION A: Single-formula truth table + truth tree
  // ==========================================================

  // User input for a single formula (e.g. "(p ^ q) -> r")
  const [formula, setFormula] = useState("p -> q");

  // Displays "Loading..." or error messages
  const [status, setStatus] = useState("");

  // Stores returned truth table
  const [table, setTable] = useState<TruthTableResponse | null>(null);

  // Stores returned truth tree JSON (single formula)
  const [treeResp, setTreeResp] = useState<any | null>(null);

  // ==========================================================
  // SECTION B: Argument truth tree (premises + conclusion)
  // ==========================================================

  // Up to 3 premises (premise 1 required, 2 and 3 optional)
  const [prem1, setPrem1] = useState("P v Q");
  const [prem2, setPrem2] = useState("P -> R");
  const [prem3, setPrem3] = useState("~Q v R");

  // Conclusion (required)
  const [concl, setConcl] = useState("R");

  // Stores returned argument tableau JSON
  const [argTree, setArgTree] = useState<any | null>(null);

  // ==========================================================
  // Helper: stable list of vars for table headers
  // ==========================================================
  const variables = useMemo(() => (table ? table.variables : []), [table]);

  // ==========================================================
  // ACTION 1: Generate Truth Table + Truth Tree (single formula)
  // ==========================================================
  async function runSingleFormula() {
    setStatus("Loading...");
    setTable(null);
    setTreeResp(null);

    try {
      // ----- Truth table -----
      const data = (await getTruthTable(formula)) as TruthTableResponse;

      if ((data as any)?.error) {
        setStatus(`Error: ${(data as any).error}`);
        return;
      }

      setTable(data);

      // ----- Truth tree (single formula) -----
      const tr = await getTruthTree(formula);
      setTreeResp(tr);

      // If backend returns error field, show it
      if (tr?.error) {
        setStatus(`Error: ${tr.error}`);
        return;
      }

      setStatus("");
    } catch (e: any) {
      setStatus(`Error: ${e?.message ?? String(e)}`);
    }
  }

  // ==========================================================
  // ACTION 2: Generate Argument Truth Tree (premises + conclusion)
  // ==========================================================
  async function runArgumentTree() {
    setStatus("Loading...");
    setArgTree(null);

    try {
      // Clean up inputs: trim whitespace and remove empty optional premises
      const premises = [prem1, prem2, prem3].map((s) => s.trim()).filter(Boolean);
      const conclusion = concl.trim();

      // Call backend
      const data = await getArgumentTree(premises, conclusion);

      if (data?.error) {
        setStatus(`Error: ${data.error}`);
        return;
      }

      setArgTree(data);
      setStatus("");
    } catch (e: any) {
      setStatus(`Error: ${e?.message ?? String(e)}`);
    }
  }

  // ==========================================================
  // Renderer 1: Single-formula truth tree (simple indentation)
  // ==========================================================
  function renderTree(node: any, indent = 0) {
    if (!node) return <Text>(no tree)</Text>;

    const marker = node.closed ? "×" : "•";

    return (
      <View style={{ marginLeft: indent * 14, marginTop: 4 }}>
        <Text>
          {marker} {node.label}
        </Text>

        {Array.isArray(node.children) &&
          node.children.map((child: any, i: number) => (
            <View key={i}>{renderTree(child, indent + 1)}</View>
          ))}
      </View>
    );
  }

  // ==========================================================
  // Renderer 2: Argument truth tree (includes line numbers)
  // ==========================================================
  function renderArgNode(node: any, indent = 0) {
    if (!node) return null;

    const pad = indent * 14;
    const marker = node.closed ? "×" : "•";

    return (
      <View style={{ marginLeft: pad, marginTop: 6 }}>
        <Text>
          ({node.line}) {marker} {node.label}
          {node.note ? ` ${node.note}` : ""}
        </Text>

        {Array.isArray(node.children) &&
          node.children.map((c: any, i: number) => (
            <View key={i}>{renderArgNode(c, indent + 1)}</View>
          ))}
      </View>
    );
  }

  // ==========================================================
  // UI
  // ==========================================================
  return (
    <SafeAreaView style={{ flex: 1, padding: 16 }}>
      <ScrollView>

        {/* ===================== Syntax Help Box ===================== */}
        <View
          style={{
            borderWidth: 1,
            borderColor: "#bbb",
            borderRadius: 10,
            padding: 12,
            marginBottom: 14,
          }}
        >
          <Text style={{ fontWeight: "700", marginBottom: 6 }}>Syntax key</Text>

          <Text>NOT: ~p  or  !p</Text>
          <Text>AND: p ^ q  or  p & q</Text>
          <Text>OR:  p v q  or  p | q</Text>
          <Text>IMPLIES: p -&gt; q (spaces optional)</Text>
          <Text>IFF: p &lt;-&gt; q</Text>

          <Text style={{ marginTop: 6, color: "#555" }}>
            Tip: Use parentheses like (p ^ q) -&gt; r
          </Text>
        </View>

        {/* ===================== Header ===================== */}
        <Text style={{ fontSize: 20, fontWeight: "700", marginBottom: 10 }}>
          Truth Table + Truth Tree
        </Text>

        {/* ===================== Single Formula Input ===================== */}
        <Text style={{ marginBottom: 6 }}>Enter a formula:</Text>
        <TextInput
          value={formula}
          onChangeText={setFormula}
          placeholder="e.g. (p ^ q) -> r"
          autoCapitalize="none"
          autoCorrect={false}
          style={{
            borderWidth: 1,
            borderColor: "#ccc",
            padding: 12,
            borderRadius: 8,
            marginBottom: 10,
          }}
        />
        <Button title="Generate (Table + Tree)" onPress={runSingleFormula} />

        {/* ===================== Status / Errors ===================== */}
        {status ? (
          <Text
            style={{
              marginTop: 12,
              color: status.startsWith("Error") ? "crimson" : "#333",
            }}
          >
            {status}
          </Text>
        ) : null}

        {/* ===================== Truth Table Output ===================== */}
        {table ? (
          <View
            style={{
              marginTop: 16,
              borderWidth: 1,
              borderColor: "#bbb",
              borderRadius: 10,
              padding: 12,
            }}
          >
            <Text style={{ fontWeight: "700", marginBottom: 10 }}>
              Truth table
            </Text>

            {/* Header row */}
            <View style={{ flexDirection: "row", marginBottom: 6 }}>
              {variables.map((v) => (
                <Text key={v} style={{ width: 55, fontWeight: "700" }}>
                  {v}
                </Text>
              ))}
              <Text style={{ width: 70, fontWeight: "700" }}>Value</Text>
            </View>

            {/* Data rows */}
            {table.rows.map((row, idx) => (
              <View key={idx} style={{ flexDirection: "row", marginBottom: 2 }}>
                {variables.map((v) => (
                  <Text key={v} style={{ width: 55 }}>
                    {row.assignment[v] ? "T" : "F"}
                  </Text>
                ))}
                <Text style={{ width: 70 }}>{row.value ? "T" : "F"}</Text>
              </View>
            ))}
          </View>
        ) : null}

        {/* ===================== Truth Tree Output (single formula) ===================== */}
        <View
          style={{
            marginTop: 16,
            borderWidth: 1,
            borderColor: "#bbb",
            borderRadius: 10,
            padding: 12,
          }}
        >
          <Text style={{ fontWeight: "700", marginBottom: 6 }}>Truth tree</Text>

          {!treeResp ? (
            <Text style={{ color: "#555" }}>
              Generate a formula to see the truth tree.
            </Text>
          ) : treeResp.error ? (
            <Text style={{ color: "crimson" }}>Error: {treeResp.error}</Text>
          ) : (
            <>
              {/* Optional helper from backend */}
              {treeResp.nnf ? (
                <Text style={{ marginBottom: 8, color: "#555" }}>
                  NNF: {treeResp.nnf}
                </Text>
              ) : null}

              {renderTree(treeResp.tree)}
            </>
          )}
        </View>

        {/* ===================== Argument Truth Tree (premises + conclusion) ===================== */}
        <View
          style={{
            marginTop: 16,
            borderWidth: 1,
            borderColor: "#bbb",
            borderRadius: 10,
            padding: 12,
            marginBottom: 30,
          }}
        >
          <Text style={{ fontWeight: "700", marginBottom: 8 }}>
            Argument truth tree
          </Text>

          <Text style={{ marginBottom: 4 }}>Premise 1 (required):</Text>
          <TextInput
            value={prem1}
            onChangeText={setPrem1}
            autoCapitalize="none"
            autoCorrect={false}
            style={{
              borderWidth: 1,
              borderColor: "#ccc",
              padding: 10,
              borderRadius: 8,
              marginBottom: 8,
            }}
          />

          <Text style={{ marginBottom: 4 }}>Premise 2 (optional):</Text>
          <TextInput
            value={prem2}
            onChangeText={setPrem2}
            autoCapitalize="none"
            autoCorrect={false}
            style={{
              borderWidth: 1,
              borderColor: "#ccc",
              padding: 10,
              borderRadius: 8,
              marginBottom: 8,
            }}
          />

          <Text style={{ marginBottom: 4 }}>Premise 3 (optional):</Text>
          <TextInput
            value={prem3}
            onChangeText={setPrem3}
            autoCapitalize="none"
            autoCorrect={false}
            style={{
              borderWidth: 1,
              borderColor: "#ccc",
              padding: 10,
              borderRadius: 8,
              marginBottom: 8,
            }}
          />

          <Text style={{ marginBottom: 4 }}>Conclusion (required):</Text>
          <TextInput
            value={concl}
            onChangeText={setConcl}
            autoCapitalize="none"
            autoCorrect={false}
            style={{
              borderWidth: 1,
              borderColor: "#ccc",
              padding: 10,
              borderRadius: 8,
              marginBottom: 10,
            }}
          />

          <Button
            title="Generate Truth Tree (Argument)"
            onPress={runArgumentTree}
          />

          {/* Initial numbered lines: premises + negated conclusion */}
          {argTree?.initial ? (
            <View style={{ marginTop: 12 }}>
              <Text style={{ fontWeight: "700", marginBottom: 6 }}>
                Setup lines
              </Text>
              {argTree.initial.map((ln: any) => (
                <Text key={ln.line}>
                  ({ln.line}) {ln.label}
                  {ln.note ? ` ${ln.note}` : ""}
                </Text>
              ))}
            </View>
          ) : null}

          {/* The actual tableau tree */}
          {argTree?.tree ? (
            <View style={{ marginTop: 10 }}>
              <Text style={{ fontWeight: "700", marginBottom: 6 }}>
                Tree
              </Text>
              {renderArgNode(argTree.tree)}
            </View>
          ) : null}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}
