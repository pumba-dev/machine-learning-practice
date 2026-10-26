<#
.SYNOPSIS
Exporta um .pptx para PDF pelo PowerPoint instalado, para validar os slides como o PowerPoint os desenha.

.EXAMPLE
powershell -File scripts/export_slides_pdf.ps1 slides/apresentacao.pptx
Grava slides/apresentacao.pdf ao lado do .pptx. Use -Pdf para outro caminho.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$Pptx,
    [string]$Pdf
)

$ErrorActionPreference = "Stop"
$source = (Resolve-Path -LiteralPath $Pptx).Path
if (-not $Pdf) { $Pdf = [IO.Path]::ChangeExtension($source, ".pdf") }
$Pdf = [IO.Path]::GetFullPath($Pdf)

$app = New-Object -ComObject PowerPoint.Application
try {
    # Open(arquivo, somente leitura, sem título, sem janela): -1 = verdadeiro, 0 = falso.
    $presentation = $app.Presentations.Open($source, -1, 0, 0)
    try {
        $presentation.SaveAs($Pdf, 32)  # 32 = ppSaveAsPDF
    }
    finally {
        $presentation.Close()
    }
}
finally {
    # Se o usuário já tinha o PowerPoint aberto com outros arquivos, não fecha o programa dele.
    if ($app.Presentations.Count -eq 0) { $app.Quit() }
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
Write-Output "PDF: $Pdf"
