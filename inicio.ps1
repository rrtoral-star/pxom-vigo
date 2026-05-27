# PXOM-SOLO - Script de Inicio Rápido
# Encoding: UTF-8

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "PXOM-SOLO - Sistema de Consulta de Normativa Urbanística" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Activar entorno virtual
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "✓ Entorno virtual activado" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✗ Error: No se encuentra el entorno virtual" -ForegroundColor Red
    Write-Host "  Ejecuta: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit
}

function Show-Menu {
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "HERRAMIENTAS DISPONIBLES" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " 1. Buscar por palabra clave"
    Write-Host " 2. Consultar artículo completo"
    Write-Host " 3. Ver grafo de conexiones"
    Write-Host " 4. Estadísticas globales"
    Write-Host " 5. Regenerar datos (extraer PDF)"
    Write-Host " 6. Salir"
    Write-Host ""
}

do {
    Show-Menu
    $opcion = Read-Host "Selecciona una opción (1-6)"
    Write-Host ""
    
    switch ($opcion) {
        "1" {
            $termino = Read-Host "Término a buscar"
            python buscar.py "$termino"
            Write-Host ""
            Read-Host "Presiona Enter para continuar"
        }
        "2" {
            $numero = Read-Host "Número de artículo (ej: 34 o 62.6)"
            python consultar.py $numero
            Write-Host ""
            Read-Host "Presiona Enter para continuar"
        }
        "3" {
            $numero = Read-Host "Número de artículo"
            python consultar_grafo.py $numero
            Write-Host ""
            Read-Host "Presiona Enter para continuar"
        }
        "4" {
            python grafo_referencias.py
            Write-Host ""
            Read-Host "Presiona Enter para continuar"
        }
        "5" {
            $confirm = Read-Host "⚠ Esto regenerará todos los datos. ¿Continuar? (S/N)"
            if ($confirm -eq "S" -or $confirm -eq "s") {
                python src\pdf_extractor.py
                Write-Host ""
                Read-Host "Presiona Enter para continuar"
            }
        }
        "6" {
            Write-Host "¡Hasta luego!" -ForegroundColor Cyan
            break
        }
        default {
            Write-Host "✗ Opción inválida" -ForegroundColor Red
            Write-Host ""
        }
    }
} while ($opcion -ne "6")