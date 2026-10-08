import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router"

import "@/index.css"
import App from "@/App"
import { crearClienteConsultas } from "@/api/consultas"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"

const clienteConsultas = crearClienteConsultas()

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={clienteConsultas}>
      <BrowserRouter>
        <TooltipProvider>
          <App />
          <Toaster position="bottom-right" />
        </TooltipProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
