$condaEnvName = 'WutheringWavesAssistant'
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
    conda create --name $condaEnvName python=3.12 -y
}

conda activate $condaEnvName

$poetryVersion = "2.1.1"
Write-Host "Conda is installing Poetry version $poetryVersion..."
conda install poetry=$poetryVersion -c conda-forge -y

poetry config virtualenvs.create false
Write-Host "Set poetry config virtualenvs.create to false."

#$cudatoolkitVersion = "11.8.0"
#Write-Host "Conda is installing cudatoolkit version $cudatoolkitVersion..."
#conda install cudatoolkit=$cudatoolkitVersion -y
#
#$cudnnVersion = "8.9.2.26"
#$cudnnBuild = "cuda11_0"
#Write-Host "Conda is installing cudnn version $cudnnVersion build $cudnnBuild..."
#conda install cudnn=$cudnnVersion=$cudnnBuild -y
#
#$zlibwapiVersion = "1.3.1"
#Write-Host "Conda is installing zlib-wapi version $zlibwapiVersion..."
#conda install zlib-wapi=$zlibwapiVersion -c conda-forge -y
#
#Write-Host "`nListing installed versions of CUDA:"
#conda list | Select-String -Pattern "cudatoolkit|cudnn|poetry"

#$poetryExtra = "dev"
#poetry install -E $poetryExtra
poetry install
#poetry install -E cuda
#poetry install -E dml

Write-Host "`nInstallation completed."
