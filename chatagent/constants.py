"""Constantes globais do ChatAgent."""

SITES_IA = {
    '1': ('ChatGPT', 'https://chatgpt.com'),
    '2': ('Gemini', 'https://gemini.google.com/u/1/app'),
    '3': ('DeepSeek', 'https://chat.deepseek.com'),
}

DIRETORIOS_IGNORADOS = {
    '.git', '.idea', '.vscode', 'node_modules', 'target', 'build',
    'dist', 'out', '.gradle', '.mvn', '__pycache__', '.venv', 'venv',
    'coverage', '.angular', '.next', 'bin', 'obj',
}

EXTENSOES_TEXTO = {
    '.java', '.kt', '.kts', '.groovy', '.xml', '.yml', '.yaml', '.properties',
    '.json', '.md', '.txt', '.py', '.js', '.jsx', '.ts', '.tsx', '.html',
    '.css', '.scss', '.sass', '.sql', '.sh', '.bat', '.cmd', '.ps1', '.toml',
    '.ini', '.cfg', '.conf', '.gradle', '.tf', '.hcl', '.dockerfile', '.gitignore',
    '.env.example', '.feature', '.graphql', '.proto', '.vue', '.svelte', '.cs',
    '.go', '.rs', '.php', '.rb', '.c', '.h', '.cpp', '.hpp',
}

NOMES_TEXTO = {
    'pom.xml', 'mvnw', 'mvnw.cmd', 'gradlew', 'gradlew.bat', 'dockerfile',
    'makefile', '.gitignore', '.dockerignore', '.editorconfig', 'jenkinsfile',
    'procfile', 'license', 'readme', 'readme.md',
}
