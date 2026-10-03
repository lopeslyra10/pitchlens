<#
.SYNOPSIS
    Acompanha um treino que está rodando solto, sem interferir nele.

.DESCRIPTION
    Os treinos longos do PitchLens rodam destacados da sessão (Start-Process), escrevendo em
    runs\*.log e runs\*.err. Este script só lê esses arquivos e a GPU, então pode ser aberto e
    fechado à vontade: Ctrl+C encerra o acompanhamento, nunca o treino.

.EXAMPLE
    .\scriptscompanhar-treino.ps1
    .\scriptscompanhar-treino.ps1 -Log runs\keypoints.log -Erro runs\keypoints.err
#>
param(
    [string]$Log = "runs\keypoints-resume.log",
    [string]$Erro = "runs\keypoints-resume.err",
    [string]$Pesos = "runs\keypoints",
    [int]$Intervalo = 30,
    [switch]$UmaVez
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

function Ler-Epoca($arquivo) {
    if (-not (Test-Path $arquivo)) { return $null }
    $achado = Select-String -Path $arquivo -Pattern 'Epoch (\d+)/(\d+)' -AllMatches | Select-Object -Last 1
    if (-not $achado) { return $null }
    $grupos = $achado.Matches[$achado.Matches.Count - 1].Groups
    return @{ Atual = [int]$grupos[1].Value; Total = [int]$grupos[2].Value }
}

function Ler-Melhor($arquivo) {
    if (-not (Test-Path $arquivo)) { return $null }
    $achado = Select-String -Path $arquivo -Pattern 'New best score: ([0-9.]+)' | Select-Object -Last 1
    if (-not $achado) { return $null }
    return [double]$achado.Matches[0].Groups[1].Value
}

function Ler-Gpu() {
    try {
        $linha = (nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader) | Select-Object -First 1
        return $linha.Trim()
    } catch { return "nvidia-smi indisponível" }
}

$inicio = Get-Date
$primeiraEpoca = $null
$ritmo = $null

while ($true) {
    $epoca = Ler-Epoca $Log
    $melhor = Ler-Melhor $Erro
    $vivo = if (Test-Path $Log) { (Get-Item $Log).LastWriteTime } else { $null }
    $treinando = @(Get-Process python -ErrorAction SilentlyContinue).Count -gt 0

    if ($epoca -and -not $primeiraEpoca) { $primeiraEpoca = @{ Numero = $epoca.Atual; Quando = Get-Date } }
    if ($epoca -and $primeiraEpoca -and $epoca.Atual -gt $primeiraEpoca.Numero) {
        $minutos = ((Get-Date) - $primeiraEpoca.Quando).TotalMinutes
        $ritmo = $minutos / ($epoca.Atual - $primeiraEpoca.Numero)
    }

    Clear-Host
    Write-Host ("PitchLens · acompanhando o treino".PadRight(44)) -NoNewline -ForegroundColor Green
    Write-Host (Get-Date -Format "HH:mm:ss")
    Write-Host ("-" * 60) -ForegroundColor DarkGray

    if ($epoca) {
        $barra = [int](20.0 * $epoca.Atual / $epoca.Total)
        Write-Host ("época        {0} / {1}  [{2}{3}]" -f $epoca.Atual, $epoca.Total, ("#" * $barra), ("." * (20 - $barra)))
    } else {
        Write-Host "época        ainda não apareceu no log"
    }
    if ($melhor -ne $null) { Write-Host ("melhor mAP   {0:N3}" -f $melhor) }
    if ($vivo) {
        $segundos = [int]((Get-Date) - $vivo).TotalSeconds
        Write-Host ("último sinal {0:HH:mm:ss}  (há {1} s)" -f $vivo, $segundos)
    }
    Write-Host ("processo     " + $(if ($treinando) { "python rodando" } else { "nenhum python rodando" })) -ForegroundColor $(if ($treinando) { "Gray" } else { "Yellow" })
    Write-Host ("GPU          " + (Ler-Gpu))
    if ($ritmo -and $epoca) {
        $faltam = ($epoca.Total - $epoca.Atual) * $ritmo
        Write-Host ("ritmo        {0:N1} min por época · fim por volta de {1:HH:mm}" -f $ritmo, (Get-Date).AddMinutes($faltam))
    }
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host "Ctrl+C sai daqui; o treino continua rodando." -ForegroundColor DarkGray

    if ($UmaVez) { break }
    Start-Sleep -Seconds $Intervalo
}
