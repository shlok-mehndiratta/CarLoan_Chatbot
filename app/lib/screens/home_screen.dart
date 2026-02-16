import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import '../models/contract_model.dart';
import 'result_screen.dart';

class HomeScreen extends StatefulWidget {
  final Function(ContractAnalysis)? onAnalysisComplete;

  const HomeScreen({super.key, this.onAnalysisComplete});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isLoading = false;
  bool _isServerConnected = false;
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _checkServerHealth();
  }

  Future<void> _checkServerHealth() async {
    final isConnected = await _apiService.checkHealth();
    if (mounted) setState(() => _isServerConnected = isConnected);
  }

  Future<void> _pickAndUploadFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf'],
      );

      if (result != null && result.files.single.path != null) {
        setState(() => _isLoading = true);

        final filePath = result.files.single.path!;
        final fileName = result.files.single.name;

        try {
          final analysis = await _apiService.uploadAndAnalyzeContract(filePath, fileName);

          // Notify parent for dashboard
          widget.onAnalysisComplete?.call(analysis);

          if (mounted) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => ResultScreen(analysis: analysis)),
            );
          }
        } catch (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('Error: ${e.toString()}'),
                backgroundColor: Colors.red,
              ),
            );
          }
        } finally {
          if (mounted) setState(() => _isLoading = false);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analyze Contract'),
        elevation: 0,
        centerTitle: true,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            if (!_isServerConnected)
              Container(
                color: Colors.red.shade100,
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.warning, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Backend server not connected. Check API_URL in .env',
                        style: TextStyle(color: Colors.red.shade900),
                      ),
                    ),
                    TextButton(
                      onPressed: _checkServerHealth,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 20),
                  Center(
                    child: Container(
                      width: 100,
                      height: 100,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: theme.primaryColor.withOpacity(0.1),
                      ),
                      child: Icon(Icons.description, size: 50, color: theme.primaryColor),
                    ),
                  ),
                  const SizedBox(height: 32),
                  Text('Upload Contract', style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload your car lease or loan contract PDF. Our AI will extract key terms, identify red flags, calculate fairness, and suggest negotiation strategies.',
                    style: TextStyle(fontSize: 14, color: Colors.grey),
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : _pickAndUploadFile,
                      icon: _isLoading
                          ? const SizedBox(
                              width: 20, height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.upload_file),
                      label: Text(_isLoading ? 'Analyzing...' : 'Select PDF & Analyze'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        backgroundColor: theme.primaryColor,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // What We Analyze
                  Card(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'What We Analyze',
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 12),
                          _buildFeatureRow(Icons.percent, 'Interest rates & APR'),
                          _buildFeatureRow(Icons.payments, 'Monthly payments & down payment'),
                          _buildFeatureRow(Icons.access_time, 'Lease terms & mileage allowance'),
                          _buildFeatureRow(Icons.cancel, 'Early termination clauses'),
                          _buildFeatureRow(Icons.build, 'Warranty & maintenance coverage'),
                          _buildFeatureRow(Icons.warning_amber, 'Red flags & unfair terms'),
                          _buildFeatureRow(Icons.shield, 'Overall fairness score'),
                          _buildFeatureRow(Icons.chat, 'Negotiation strategies'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Colors.green),
          const SizedBox(width: 10),
          Text(text, style: const TextStyle(fontSize: 14)),
        ],
      ),
    );
  }
}