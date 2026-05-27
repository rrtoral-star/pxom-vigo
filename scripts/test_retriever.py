# scripts\test_retriever.py
import sys
sys.path.insert(0, 'src')

if __name__ == '__main__':
    from retriever import RAGRetriever
    r = RAGRetriever()
    
    print("\n=== SIN FILTRO ===")
    resultados = r.buscar("altura máxima en zona residencial", top_k=5, verbose=True)
    r.mostrar_resultados(resultados)

    print("\n=== FILTRO fuente=pxom ===")
    resultados = r.buscar("altura máxima en zona residencial", top_k=5, filtros={"fuente": "pxom"}, verbose=True)
    r.mostrar_resultados(resultados)

    print("\n=== FILTRO fuente=cte ===")
    resultados = r.buscar("altura máxima en zona residencial", top_k=5, filtros={"fuente_prefijo": "cte"}, verbose=True)
    r.mostrar_resultados(resultados)