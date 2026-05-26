#!/usr/bin/env python
"""
Bulk Evaluation Script — Fase 5
Avalia a qualidade das respostas do sistema usando um dataset fixo e salva métricas.
Isso pode ser integrado ao LangSmith ou executado localmente.
"""
import asyncio
import sys
import json
import uuid
import time
from pathlib import Path
from rich.console import Console
from rich.table import Table

# Ajusta path para importar módulos do backend
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.agent.graph import run_analytics
from app.agent.evaluators import evaluate_relevance

console = Console()

# Dataset de teste (Exemplo)
EVAL_DATASET = [
    {
        "question": "Qual foi a margem da safra 2026-03?",
        "expected_intent": "analytics",
    },
    {
        "question": "O que é ROAE?",
        "expected_intent": "conceptual",
    },
    {
        "question": "Me dê a receita da pizza marguerita.",
        "expected_intent": "rejected",
    }
]


async def evaluate_dataset():
    console.print("[bold blue]Iniciando avaliação contínua (Fase 5)...[/bold blue]\n")
    
    table = Table(title="Resultados da Avaliação")
    table.add_column("Query", style="cyan", max_width=40)
    table.add_column("Intent", justify="center")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Relevance Score", justify="right")
    table.add_column("Status", justify="center")

    total_score = 0.0
    passed = 0
    
    for item in EVAL_DATASET:
        question = item["question"]
        expected_intent = item["expected_intent"]
        
        start_time = time.time()
        
        try:
            # Executa a query no Swarm
            trace_id = str(uuid.uuid4())
            result = await run_analytics(question, trace_id=trace_id)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Avalia relevância
            eval_result = await evaluate_relevance(question, result["answer"])
            score = eval_result["score"]
            is_relevant = eval_result["is_relevant"]
            
            # Ajusta validação dependendo da intenção esperada
            if expected_intent == "rejected" and "rejected" in result.get("routed_path", ""):
                is_relevant = True
                score = 1.0
                
            total_score += score
            if is_relevant:
                passed += 1
                status = "[green]PASS[/green]"
            else:
                status = "[red]FAIL[/red]"
                
            table.add_row(
                question,
                result.get("routed_path", "unknown"),
                str(latency_ms),
                f"{score:.2f}",
                status
            )
            
        except Exception as e:
            table.add_row(
                question,
                "ERROR",
                "-",
                "0.00",
                f"[red]FAIL: {e}[/red]"
            )

    console.print(table)
    
    avg_score = total_score / len(EVAL_DATASET)
    console.print(f"\n[bold]Média de Relevância:[/bold] {avg_score:.2f}")
    console.print(f"[bold]Taxa de Sucesso:[/bold] {passed}/{len(EVAL_DATASET)} ({(passed/len(EVAL_DATASET))*100:.1f}%)")
    
    # Salvar relatório no disco
    report = {
        "timestamp": time.time(),
        "total_evaluated": len(EVAL_DATASET),
        "passed": passed,
        "average_relevance": avg_score
    }
    with open("eval_report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    console.print("[green]Avaliação concluída e salva em eval_report.json[/green]")
    
    if passed < len(EVAL_DATASET):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(evaluate_dataset())
