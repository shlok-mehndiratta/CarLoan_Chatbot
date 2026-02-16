import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/contract_model.dart';
import 'negotiation_chat_screen.dart';

/// Dashboard that shows a summary of the latest analysis and
/// provides quick actions to navigate to other features.
class ComparisonDashboardScreen extends StatefulWidget {
  final ContractAnalysis? lastAnalysis;

  const ComparisonDashboardScreen({super.key, this.lastAnalysis});

  @override
  State<ComparisonDashboardScreen> createState() => _ComparisonDashboardScreenState();
}

class _ComparisonDashboardScreenState extends State<ComparisonDashboardScreen> {
  final ApiService _apiService = ApiService();
  bool _isServerOnline = false;

  @override
  void initState() {
    super.initState();
    _checkServer();
  }

  Future<void> _checkServer() async {
    final ok = await _apiService.checkHealth();
    setState(() => _isServerOnline = ok);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final analysis = widget.lastAnalysis;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(
              Icons.circle,
              size: 12,
              color: _isServerOnline ? Colors.green : Colors.red,
            ),
            onPressed: _checkServer,
            tooltip: _isServerOnline ? 'Server Online' : 'Server Offline',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Welcome card
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              color: theme.primaryColor,
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    const Icon(Icons.shield, size: 40, color: Colors.white),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Car Contract AI',
                            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Your AI-powered contract review assistant',
                            style: TextStyle(color: Colors.white.withOpacity(0.85)),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Latest analysis summary
            if (analysis != null) ...[
              Text('Latest Analysis', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.description, size: 20),
                          const SizedBox(width: 8),
                          Expanded(child: Text(analysis.fileName, style: const TextStyle(fontWeight: FontWeight.w600))),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _buildScoreChip(analysis.fairness),
                          const SizedBox(width: 12),
                          Expanded(child: Text(analysis.fairness.summary, style: const TextStyle(fontSize: 13))),
                        ],
                      ),
                      if (analysis.sla.redFlags.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: analysis.sla.redFlags.map((f) => Chip(
                            label: Text(f, style: const TextStyle(fontSize: 11)),
                            backgroundColor: Colors.red.shade50,
                            side: BorderSide(color: Colors.red.shade200),
                            visualDensity: VisualDensity.compact,
                          )).toList(),
                        ),
                      ],
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.chat, size: 18),
                          label: const Text('Start Negotiation'),
                          onPressed: () {
                            Navigator.push(context, MaterialPageRoute(
                              builder: (_) => NegotiationChatScreen(
                                contractId: analysis.contractId,
                                contractName: analysis.fileName,
                              ),
                            ));
                          },
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // Quick actions
            Text('Quick Actions', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.3,
              children: [
                _buildActionCard(
                  theme,
                  icon: Icons.upload_file,
                  title: 'Analyze Contract',
                  subtitle: 'Upload a PDF',
                  color: Colors.blue,
                  onTap: () => DefaultTabController.of(context).animateTo(0),
                ),
                _buildActionCard(
                  theme,
                  icon: Icons.directions_car,
                  title: 'VIN Lookup',
                  subtitle: 'Check vehicle history',
                  color: Colors.teal,
                  onTap: () => DefaultTabController.of(context).animateTo(1),
                ),
                _buildActionCard(
                  theme,
                  icon: Icons.attach_money,
                  title: 'Price Estimate',
                  subtitle: 'Fair market value',
                  color: Colors.green,
                  onTap: () => DefaultTabController.of(context).animateTo(2),
                ),
                _buildActionCard(
                  theme,
                  icon: Icons.info,
                  title: 'How It Works',
                  subtitle: 'Features & tips',
                  color: Colors.purple,
                  onTap: () => _showHowItWorks(context),
                ),
              ],
            ),

            const SizedBox(height: 24),

            // Stats section
            Text('Features', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            ..._buildFeaturesList(),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreChip(FairnessScore fairness) {
    return Container(
      width: 56,
      height: 56,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: fairness.getScoreColor().withOpacity(0.15),
        border: Border.all(color: fairness.getScoreColor(), width: 2),
      ),
      child: Center(
        child: Text(
          '${fairness.score.toInt()}',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: fairness.getScoreColor(),
          ),
        ),
      ),
    );
  }

  Widget _buildActionCard(ThemeData theme, {
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 28, color: color),
              const Spacer(),
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 2),
              Text(subtitle, style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildFeaturesList() {
    final features = [
      {'icon': Icons.description, 'title': 'Contract Analysis', 'desc': 'AI extracts key terms from your car lease/loan PDF'},
      {'icon': Icons.shield, 'title': 'Fairness Score', 'desc': 'Rates your contract on a 0-100 scale with detailed breakdown'},
      {'icon': Icons.directions_car, 'title': 'VIN Intelligence', 'desc': 'Decode any VIN for vehicle specs, recalls, and complaints'},
      {'icon': Icons.attach_money, 'title': 'Price Estimation', 'desc': 'Fair market value based on make, model, year, and condition'},
      {'icon': Icons.chat, 'title': 'Negotiation Chat', 'desc': 'AI-powered negotiation advisor with specific strategies'},
      {'icon': Icons.email, 'title': 'Email Generator', 'desc': 'Professional negotiation emails drafted automatically'},
    ];

    return features.map((f) => Card(
      margin: const EdgeInsets.only(bottom: 8),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: ListTile(
        leading: Icon(f['icon'] as IconData, color: Theme.of(context).primaryColor),
        title: Text(f['title'] as String, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        subtitle: Text(f['desc'] as String, style: const TextStyle(fontSize: 12)),
      ),
    )).toList();
  }

  void _showHowItWorks(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('How It Works'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('1. Upload your car lease/loan contract PDF'),
              SizedBox(height: 8),
              Text('2. AI extracts key terms and calculates fairness'),
              SizedBox(height: 8),
              Text('3. Check the VIN for vehicle history and recalls'),
              SizedBox(height: 8),
              Text('4. Get fair market value estimation'),
              SizedBox(height: 8),
              Text('5. Chat with AI for negotiation strategies'),
              SizedBox(height: 8),
              Text('6. Generate professional negotiation emails'),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Got it!')),
        ],
      ),
    );
  }
}
