import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// `base: "./"` gera caminhos relativos: o mesmo build funciona em
// https://lopeslyra10.github.io/pitchlens/ e em qualquer servidor local.
export default defineConfig({
  base: "./",
  plugins: [react()],
  test: {
    environment: "node",
  },
});
