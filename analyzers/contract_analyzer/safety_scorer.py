"""
Safety Scorer
Calculates overall safety score based on all analysis results
"""
from typing import Dict, Any, List


class SafetyScorer:
    """Calculate overall safety score for smart contracts"""

    def __init__(self):
        pass

    def calculate_score(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate overall safety score (0-100)

        Scoring breakdown:
        - Code Quality: 25 points
        - Security: 40 points
        - Tokenomics: 20 points
        - Liquidity: 15 points

        Args:
            analysis_results: Complete analysis results

        Returns:
            Dict with scores and risk assessment
        """
        scores = {
            'code_quality_score': 0,
            'security_score': 0,
            'tokenomics_score': 0,
            'liquidity_score': 0,
            'overall_score': 0,
            'risk_level': 'unknown',
            'risk_color': 'gray',
            'recommendation': ''
        }

        # Code Quality Score (25 points)
        scores['code_quality_score'] = self._calculate_code_quality_score(analysis_results)

        # Security Score (40 points)
        scores['security_score'] = self._calculate_security_score(analysis_results)

        # Tokenomics Score (20 points)
        scores['tokenomics_score'] = self._calculate_tokenomics_score(analysis_results)

        # Liquidity Score (15 points) - Placeholder for now
        scores['liquidity_score'] = self._calculate_liquidity_score(analysis_results)

        # Calculate overall score
        scores['overall_score'] = (
            scores['code_quality_score'] +
            scores['security_score'] +
            scores['tokenomics_score'] +
            scores['liquidity_score']
        )

        # Determine risk level
        risk_data = self._determine_risk_level(scores['overall_score'])
        scores['risk_level'] = risk_data['level']
        scores['risk_color'] = risk_data['color']
        scores['recommendation'] = risk_data['recommendation']

        return scores

    def _calculate_code_quality_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate code quality score (max 25 points)"""
        code_quality = analysis.get('code_quality', {})

        # If code quality score already calculated, use it
        if 'score' in code_quality:
            return code_quality['score']

        score = 0

        # Verified contract (10 points)
        if analysis.get('is_verified'):
            score += 10

        # Modern compiler (5 points)
        if code_quality.get('modern_compiler'):
            score += 5
        elif code_quality.get('compiler_version'):
            score += 3

        # Optimization enabled (5 points)
        if code_quality.get('optimization_enabled'):
            score += 5

        # Has license (5 points)
        if code_quality.get('license') and code_quality.get('license') != 'None':
            score += 5

        return min(score, 25)

    def _calculate_security_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate security score (max 40 points)"""
        vulnerabilities = analysis.get('vulnerabilities', [])

        # Start with max score
        score = 40

        # Deduct points based on vulnerability severity
        deductions = {
            'critical': 15,
            'high': 10,
            'medium': 5,
            'low': 2
        }

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'low')
            score -= deductions.get(severity, 2)

        # Additional deductions for specific vulnerability types
        vuln_types = [v.get('type') for v in vulnerabilities]

        if 'reentrancy' in vuln_types:
            score -= 5  # Extra penalty for reentrancy

        if 'honeypot_pattern' in vuln_types:
            score -= 10  # Heavy penalty for honeypot patterns

        # Bonus for no vulnerabilities
        if len(vulnerabilities) == 0:
            score = 40

        return max(score, 0)

    def _calculate_tokenomics_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate tokenomics score (max 20 points)"""
        tokenomics = analysis.get('tokenomics', {})

        # If tokenomics score already calculated, use it
        if 'score' in tokenomics:
            return tokenomics['score']

        score = 20  # Start with perfect score

        # Deduct for red flags
        red_flags = tokenomics.get('red_flags', [])
        score -= len(red_flags) * 4

        # Deduct for warnings
        warnings = tokenomics.get('warnings', [])
        score -= len(warnings) * 2

        return max(score, 0)

    def _calculate_liquidity_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate liquidity score (max 15 points)"""
        liquidity = analysis.get('liquidity', {})

        score = 0

        # Liquidity locked (10 points)
        if liquidity.get('is_locked'):
            score += 10

            # Bonus for lock duration
            lock_days = liquidity.get('lock_duration_days', 0)
            if lock_days >= 365:
                score += 3
            elif lock_days >= 180:
                score += 2
            elif lock_days >= 90:
                score += 1

            # Bonus for lock percentage
            lock_percentage = liquidity.get('lock_percentage', 0)
            if lock_percentage >= 90:
                score += 2
            elif lock_percentage >= 70:
                score += 1
        else:
            # No liquidity lock is a major red flag
            # We'll still give some points if other factors are good
            score = 0

        return min(score, 15)

    def _determine_risk_level(self, overall_score: int) -> Dict[str, str]:
        """Determine risk level based on overall score"""
        if overall_score >= 85:
            return {
                'level': 'very_low',
                'color': 'green',
                'recommendation': 'Contract appears to be safe with minimal risks detected. Always DYOR.'
            }
        elif overall_score >= 70:
            return {
                'level': 'low',
                'color': 'lightgreen',
                'recommendation': 'Contract appears relatively safe but has some minor concerns. Review carefully.'
            }
        elif overall_score >= 50:
            return {
                'level': 'medium',
                'color': 'yellow',
                'recommendation': 'Exercise caution. Contract has notable concerns that should be reviewed.'
            }
        elif overall_score >= 30:
            return {
                'level': 'high',
                'color': 'orange',
                'recommendation': 'High risk detected. Multiple serious concerns found. Invest with extreme caution.'
            }
        else:
            return {
                'level': 'critical',
                'color': 'red',
                'recommendation': 'CRITICAL RISK! Contract has severe security issues. Do not invest without thorough review.'
            }

    def get_detailed_breakdown(self, scores: Dict[str, Any]) -> List[str]:
        """Get detailed breakdown of score components"""
        breakdown = []

        breakdown.append(f"Code Quality: {scores['code_quality_score']}/25")
        breakdown.append(f"Security: {scores['security_score']}/40")
        breakdown.append(f"Tokenomics: {scores['tokenomics_score']}/20")
        breakdown.append(f"Liquidity: {scores['liquidity_score']}/15")
        breakdown.append(f"Overall: {scores['overall_score']}/100")

        return breakdown

    def get_priority_issues(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get priority issues that need attention"""
        priority_issues = []

        # Critical vulnerabilities
        vulnerabilities = analysis_results.get('vulnerabilities', [])
        critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'critical']
        high_vulns = [v for v in vulnerabilities if v.get('severity') == 'high']

        for vuln in critical_vulns:
            priority_issues.append({
                'severity': 'critical',
                'category': 'security',
                'issue': vuln.get('description'),
                'recommendation': vuln.get('recommendation')
            })

        for vuln in high_vulns[:3]:  # Limit to top 3 high severity
            priority_issues.append({
                'severity': 'high',
                'category': 'security',
                'issue': vuln.get('description'),
                'recommendation': vuln.get('recommendation')
            })

        # Tokenomics red flags
        tokenomics = analysis_results.get('tokenomics', {})
        for flag in tokenomics.get('red_flags', [])[:3]:  # Limit to top 3
            priority_issues.append({
                'severity': 'high',
                'category': 'tokenomics',
                'issue': flag,
                'recommendation': 'Review tokenomics carefully'
            })

        # No liquidity lock
        liquidity = analysis_results.get('liquidity', {})
        if not liquidity.get('is_locked'):
            priority_issues.append({
                'severity': 'critical',
                'category': 'liquidity',
                'issue': 'Liquidity is NOT locked',
                'recommendation': 'Extreme caution - developers can remove liquidity at any time'
            })

        return priority_issues
