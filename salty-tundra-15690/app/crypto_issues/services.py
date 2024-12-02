# services.py
import re
import base64
import requests
import asyncio
from datetime import datetime
from .models import Repository, CryptoIssue

class CryptoAnalyzer:
    def __init__(self, github_token):
        self.token = github_token
        self.headers = {'Authorization': f'token {github_token}'}
        self.session = requests.Session()
        self.crypto_patterns = {
            'weak_cipher': (
                r'(DES|RC4|MD5|SHA1)',
                'Weak cryptographic algorithm detected',
                'critical'
            ),
            'hardcoded_secret': (
                r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
                'Potential hardcoded secret detected',
                'high'
            ),
            'unsafe_random': (
                r'random\.|Math\.random|rand\(|srand\(',
                'Potentially unsafe random number generation',
                'medium'
            ),
            'weak_hash': (
                r'createHash\(["\']md5["\']\)|createHash\(["\']sha1["\']\)|hash\(["\']md5["\']\)',
                'Weak hashing algorithm detected',
                'high'
            ),
            'ecb_mode': (
                r'ECB|electronic codebook',
                'ECB mode encryption detected',
                'critical'
            ),
            'static_iv': (
                r'iv\s*=\s*["\'][^"\']+["\']|InitializationVector\(["\'][^"\']+["\'\])',
                'Static initialization vector detected',
                'high'
            ),
            'static_salt': (
                r'salt\s*=\s*["\'][^"\']+["\']',
                'Static salt value detected',
                'high'
            ),
            'weak_key_size': (
                r'keysize\s*=\s*\d{1,3}|key_size\s*=\s*\d{1,3}',
                'Potentially weak key size',
                'medium'
            ),
            'deprecated_crypto': (
                r'(Blowfish|RC2|RC5|IDEA)',
                'Deprecated cryptographic algorithm detected',
                'high'
            ),
            'timing_attack': (
                r'(strcmp\(|memcmp\()',
                'Potential timing attack vulnerability in string comparison',
                'medium'
            )
        }

    def analyze_repository(self, repo_url):
        match = re.match(r'https://github.com/([^/]+)/([^/]+)', repo_url)
        if not match:
            raise ValueError('Invalid GitHub repository URL')
        
        owner, name = match.groups()
        
        repo, created = Repository.objects.get_or_create(
            owner=owner,
            name=name,
            defaults={'url': repo_url}
        )
        
        try:
            repo.status = 'analyzing'
            repo.save()
            
            if asyncio.get_event_loop().is_closed():
                asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.analyze_contents_async(repo, f'https://api.github.com/repos/{owner}/{name}/contents'))
            
            repo.status = 'completed'
        except Exception as e:
            repo.status = 'error'
            repo.error_message = str(e)
        
        repo.save()
        return repo

    async def analyze_contents_async(self, repo, contents_url, path_prefix=''):
        try:
            response = self.session.get(contents_url, headers=self.headers)
            response.raise_for_status()
            contents = response.json()

            if not isinstance(contents, list):
                contents = [contents]

            tasks = []
            
            for item in contents:
                item_path = f"{path_prefix}/{item['name']}" if path_prefix else item['name']
                
                if item['type'] == 'file':
                    if self._is_analyzable_file(item['name']):
                        tasks.append(self.analyze_file_async(repo, item, item_path))
                elif item['type'] == 'dir':
                    tasks.append(self.analyze_contents_async(repo, item['url'], item_path))
            
            if tasks:
                await asyncio.gather(*tasks)
                
        except Exception as e:
            print(f"Error analyzing contents at {contents_url}: {str(e)}")

    async def analyze_file_async(self, repo, file_info, file_path):
        try:
            response = self.session.get(file_info['url'], headers=self.headers)
            response.raise_for_status()
            content = response.json()
            
            if content['encoding'] == 'base64':
                file_content = base64.b64decode(content['content']).decode('utf-8')
                await self._analyze_content(repo, file_path, file_content)
                
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")

    def _is_analyzable_file(self, filename):
        extensions = (
            '.py', '.js', '.java', '.go', '.rb', '.php', 
            '.cpp', '.c', '.h', '.cs', '.ts', '.swift', 
            '.m', '.h', '.scala', '.rs', '.kt', '.go'
        )
        return filename.lower().endswith(extensions)

    async def _analyze_content(self, repo, file_path, content):
        issues = []
        
        for pattern_name, (pattern, description, severity) in self.crypto_patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
                line_number = content[:match.start()].count('\n') + 1
                code_snippet = self._get_code_snippet(content, match)
                
                issues.append(
                    CryptoIssue(
                        repository=repo,
                        file_path=file_path,
                        line_number=line_number,
                        issue_type=pattern_name,
                        description=description,
                        severity=severity,
                        code_snippet=code_snippet,
                        recommendation=self._get_recommendation(pattern_name)
                    )
                )
        
        if issues:
            await asyncio.to_thread(CryptoIssue.objects.bulk_create, issues)

    def _get_code_snippet(self, content, match):
        lines = content.split('\n')
        line_number = content[:match.start()].count('\n')
        start_line = max(0, line_number - 2)
        end_line = min(len(lines), line_number + 3)
        return '\n'.join(lines[start_line:end_line])

    def _get_recommendation(self, issue_type):
        recommendations = {
            'weak_cipher': 'Use strong encryption algorithms like AES-256-GCM. Avoid outdated algorithms like DES, RC4, MD5, and SHA1.',
            'hardcoded_secret': 'Store sensitive information in environment variables or use a secure secret management system.',
            'unsafe_random': 'Use cryptographically secure random number generation. In Python, use secrets module instead of random.',
            'weak_hash': 'Use strong hashing algorithms like SHA-256, SHA-3, or better. Consider using specialized password hashing functions like Argon2 for passwords.',
            'ecb_mode': 'Use secure modes of operation like GCM or CBC with proper padding. ECB mode is not secure for most use cases.',
            'static_iv': 'Generate a new random IV for each encryption operation. Never reuse IVs.',
            'static_salt': 'Generate a unique random salt for each hash operation. Store the salt alongside the hash.',
            'weak_key_size': 'Use appropriate key sizes: at least 256 bits for symmetric keys, 2048 bits for RSA, 384 bits for elliptic curves.',
            'deprecated_crypto': 'Replace deprecated algorithms with modern alternatives. Consult current cryptographic standards and best practices.',
            'timing_attack': 'Use constant-time comparison functions when comparing sensitive values like hashes or tokens.'
        }
        return recommendations.get(issue_type, 'Review and update the code following current security best practices')
