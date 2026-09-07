param (
    [string]$poetryExtra
)

Set-Location $PSScriptRoot\..

try {
    $nvidiaInfo = nvidia-smi | Select-String "Driver Version"
    Write-Host "`n$nvidiaInfo`n"
} catch {
#    Write-Output "nvidia-smi not available or NVIDIA GPU not detected."
}

if (-not $poetryExtra) {
    Write-Host "Please select an option:"
#    nvidia-smi
    Write-Host "1: cu126, NVIDIA gpu RTX 40 Series, cuda12.6"
    Write-Host "2: dml, AMD gpu or NVIDIA gpu"
    Write-Host "3: cpu"
    Write-Host "4: cu118, NVIDIA gpu RTX 10/20/30 Series, cuda11.8"
    Write-Host "5: cu129, NVIDIA gpu RTX 50 Series, cuda12.9"
    Write-Host "0: exit..."

    $selectPoetryExtra = Read-Host "Enter your choice (1, 2, 3, 4, 5, or 0)"

    while ($selectPoetryExtra -notin "1", "2", "3", "4", "5", "0") {
        Write-Host "Invalid selection. Please choose 1, 2, 3, 4, 5, or 0."
        $selectPoetryExtra = Read-Host "Enter your choice (1, 2, 3, 4, 5, or 0)"
    }
#    if ($selectPoetryExtra -in "2") {
#        Write-Host "Unsupport..."
#        exit
#    }
    if ($selectPoetryExtra -eq "0") {
        Write-Host "exit..."
        exit
    }
    switch ($selectPoetryExtra) {
        "1" { $poetryExtra = "cu126" }
        "2" { $poetryExtra = "dml" }
        "3" { $poetryExtra = "cpu" }
        "4" { $poetryExtra = "cu118" }
        "5" { $poetryExtra = "cu129" }
    }
}

Write-Host "Poetry group: $poetryExtra"

$condaEnvNamePrefix = 'wwa'
$poetryExtraAll = "cu126", "dml", "cpu", "cu118", "cu129"
if ($poetryExtra -notin $poetryExtraAll) {
    Write-Host "$poetryExtra is not in valid values: $poetryExtraAll" -ForegroundColor Red
    exit
}

$condaEnvNameSubfix = $poetryExtra
if ($poetryExtra -in "cu126", "cu118", "cu129") {
    $condaEnvNameSubfix = "cuda"
} elseif ($poetryExtra -in "dml") {
    $condaEnvNameSubfix = "dml"
} else {
    $condaEnvNameSubfix = "cpu"
}
$condaEnvName = $condaEnvNamePrefix + "-" + $condaEnvNameSubfix
Write-Host "Conda virtual environment: $condaEnvName"

# Check if Conda is available
try {
    $condaVersion = conda --version
    Write-Host "Conda is available. Version: $condaVersion"
} catch {
    Write-Host "Conda is not available. Please ensure Conda is installed and added to the system PATH." -ForegroundColor Red
    exit
}

# Check if the CONDA_DEFAULT_ENV environment variable exists
if ($env:CONDA_DEFAULT_ENV) {
    Write-Host "Currently activated conda environment: $env:CONDA_DEFAULT_ENV"
    Write-Host "Deactivating the current conda environment"
    conda deactivate
}

# Retrieve all Conda environment names
$envs = conda env list | Select-String -Pattern '^\S+' | ForEach-Object { $_.Matches.Groups[0].Value }

# Check if the target environment exists
if ($envs -contains $condaEnvName) {
    conda remove --name $condaEnvName --all -y
} else {
    Write-Host "Conda virtual environment '$condaEnvName' is not found. Skipping."
}

# Initialize Conda for PowerShell if not already initialized
$condaProfilePath = (conda info --json | ConvertFrom-Json).conda_prefix + '\etc\profile.d\conda.sh'
if (-not (Test-Path $condaProfilePath)) {
    Write-Host "Initializing Conda for PowerShell..."
    conda init powershell
    Write-Host "Please restart PowerShell to complete the initialization." -ForegroundColor Red
    exit
} else {
    Write-Host "Conda is already initialized for PowerShell."
}

# Check if the target environment exists
$envs = conda env list | Select-String -Pattern '^\S+' | ForEach-Object { $_.Matches.Groups[0].Value }
if ($envs -contains $condaEnvName) {
    Write-Host "Conda virtual environment '$condaEnvName' already exists."
} else {
    Write-Host "Creating Conda virtual environment: '$condaEnvName'"
    conda create --name $condaEnvName python=3.12 -y -c defaults -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
}

conda activate $condaEnvName

$poetryVersion = "2.1.1"
Write-Host "Conda is installing Poetry version $poetryVersion..."
conda install poetry=$poetryVersion -y -c conda-forge -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/

poetry config virtualenvs.create false
Write-Host "Set poetry config virtualenvs.create to false."

if ($poetryExtra -eq "cu126") {
    #Write-Output "cuda12.4 + cudnn9.1"
    #$cudatoolkitVersion = "12.4.1"
    #Write-Host "Conda is installing cuda-toolkit version $cudatoolkitVersion..."
    #conda install cuda-toolkit=$cudatoolkitVersion -y -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
    #
    #$cudnnVersion = "9.1.1.17"
    #$cudnnBuild = "cuda12_0"
    #Write-Host "Conda is installing cudnn version $cudnnVersion build $cudnnBuild..."
    #conda install cudnn=$cudnnVersion=$cudnnBuild -y -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main

#    Write-Output "cuda12.6 + cudnn9.3"
#    $cudatoolkitVersion = "12.6.1"
#    Write-Host "Conda is installing cuda-toolkit version $cudatoolkitVersion..."
##    conda install cuda-toolkit=$cudatoolkitVersion -y -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
#    conda install cuda-toolkit=$cudatoolkitVersion -y -c nvidia -c https://mirrors.sustech.edu.cn/anaconda-extra/cloud/nvidia/
#
#    $cudnnVersion = "9.3.0.75"
#    $cudnnBuild = "cuda12.6"
#    Write-Host "Conda is installing cudnn version $cudnnVersion build $cudnnBuild..."
##    conda install cudnn=$cudnnVersion=$cudnnBuild -y -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
#    conda install cudnn=$cudnnVersion=$cudnnBuild -y -c nvidia -c https://mirrors.sustech.edu.cn/anaconda-extra/cloud/nvidia/
#
#    #$zlibwapiVersion = "1.3.1"
#    #Write-Host "Conda is installing zlib-wapi version $zlibwapiVersion..."
#    #conda install zlib-wapi=$zlibwapiVersion -y -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
#
#    Write-Host "`nListing installed versions of CUDA:"
#    conda list | Select-String -Pattern "cuda-toolkit|cudnn|poetry"

    poetry install -E cu126
} elseif ($poetryExtra -eq "cu129") {
    poetry install -E cu129
} elseif ($poetryExtra -eq "cu118") {
#    Write-Output "cuda11.8 + cudnn8.9"
#    $cudatoolkitVersion = "11.8.0"
#    Write-Host "Conda is installing cudatoolkit version $cudatoolkitVersion..."
#    conda install cudatoolkit=$cudatoolkitVersion -y -c defaults -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
#
#    $cudnnVersion = "8.9.2.26"
#    $cudnnBuild = "cuda11_0"
#    Write-Host "Conda is installing cudnn version $cudnnVersion build $cudnnBuild..."
#    conda install cudnn=$cudnnVersion=$cudnnBuild -y -c defaults -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
#
#    $zlibwapiVersion = "1.3.1"
#    Write-Host "Conda is installing zlib-wapi version $zlibwapiVersion..."
#    #conda install zlib-wapi=$zlibwapiVersion -c conda-forge -y
#    conda install zlib-wapi=$zlibwapiVersion -y -c conda-forge -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
#
#    Write-Host "`nListing installed versions of CUDA:"
#    conda list | Select-String -Pattern "cudatoolkit|cudnn|poetry"

    poetry install -E cu118
} elseif ($poetryExtra -eq "dml") {
    poetry install -E dml
} elseif ($poetryExtra -eq "cpu") {
    poetry install -E cpu
}
#poetry install -E dev

Write-Host "`nInstallation completed."
