# AI Search Agent 🚀

An intelligent AI Search Agent built using **LangGraph**, designed to perform autonomous, multi-source search and synthesis. This agent runs coordinated searches across Google, Bing, and Reddit, analyzes each result set with focused prompts, and synthesizes a combined, accurate answer for user queries.

---

## 🔍 Architecture Overview

The system follows a graph-based workflow:

1. **Receive user query**
2. **Parallel search** across Google, Bing, and Reddit
3. **Aggregate & analyze** search results individually
4. **Synchronize Reddit results**
5. **Synthesize insights** from all sources
6. **Return final answer**

This architecture enables robust, agentic search automation using graph orchestration powered by LangGraph. 

<img width="627" height="535" alt="Image" src="https://github.com/user-attachments/assets/6b03b1bd-1b7a-4e2e-bd34-b7e41dc23dbc" />

---

## ⭐️ Key Features

- 🔎 **Multi-engine search** (Google, Bing, Reddit)
- 🧠 **Focused LLM analysis** per source
- 🧩 **Graph-orchestrated workflow** using LangGraph
- 🤖 **Synthesis of insights** into cohesive answers
- ⚡ **Extensible & modular** for adding more tools

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/1rishu0/AI-Search-Agent.git
cd AI-Search-Agent
