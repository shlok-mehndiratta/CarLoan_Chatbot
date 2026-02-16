import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/contract_model.dart';

class PriceEstimationScreen extends StatefulWidget {
  const PriceEstimationScreen({super.key});

  @override
  State<PriceEstimationScreen> createState() => _PriceEstimationScreenState();
}

class _PriceEstimationScreenState extends State<PriceEstimationScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final ApiService _apiService = ApiService();

  // Manual entry fields
  final _makeController = TextEditingController();
  final _modelController = TextEditingController();
  final _yearController = TextEditingController();
  final _mileageController = TextEditingController();
  String _condition = 'good';

  // VIN entry
  final _vinController = TextEditingController();

  bool _isLoading = false;
  PriceEstimate? _result;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _makeController.dispose();
    _modelController.dispose();
    _yearController.dispose();
    _mileageController.dispose();
    _vinController.dispose();
    super.dispose();
  }

  Future<void> _estimateManual() async {
    if (_makeController.text.isEmpty || _modelController.text.isEmpty || _yearController.text.isEmpty) {
      setState(() => _error = 'Please fill in Make, Model, and Year');
      return;
    }

    setState(() { _isLoading = true; _error = null; _result = null; });

    try {
      final result = await _apiService.estimatePrice(
        make: _makeController.text.trim(),
        model: _modelController.text.trim(),
        year: int.parse(_yearController.text.trim()),
        mileage: _mileageController.text.isNotEmpty ? int.tryParse(_mileageController.text.trim()) : null,
        condition: _condition,
      );
      setState(() => _result = result);
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _estimateByVin() async {
    if (_vinController.text.trim().length != 17) {
      setState(() => _error = 'VIN must be exactly 17 characters');
      return;
    }

    setState(() { _isLoading = true; _error = null; _result = null; });

    try {
      final result = await _apiService.estimatePriceByVin(_vinController.text.trim().toUpperCase());
      setState(() => _result = result);
    } catch (e) {
      setState(() => _error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Price Estimation'),
        centerTitle: true,
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.edit), text: 'Manual'),
            Tab(icon: Icon(Icons.qr_code), text: 'By VIN'),
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildManualTab(theme),
                _buildVinTab(theme),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildManualTab(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Vehicle Details',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _makeController,
                    decoration: InputDecoration(
                      labelText: 'Make (e.g., Toyota)',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      prefixIcon: const Icon(Icons.directions_car),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _modelController,
                    decoration: InputDecoration(
                      labelText: 'Model (e.g., Camry)',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      prefixIcon: const Icon(Icons.label),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _yearController,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText: 'Year',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            prefixIcon: const Icon(Icons.calendar_today),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: TextField(
                          controller: _mileageController,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText: 'Mileage',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            prefixIcon: const Icon(Icons.speed),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text('Condition', style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  SegmentedButton<String>(
                    segments: const [
                      ButtonSegment(value: 'excellent', label: Text('Excellent')),
                      ButtonSegment(value: 'good', label: Text('Good')),
                      ButtonSegment(value: 'fair', label: Text('Fair')),
                      ButtonSegment(value: 'poor', label: Text('Poor')),
                    ],
                    selected: {_condition},
                    onSelectionChanged: (Set<String> s) => setState(() => _condition = s.first),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : _estimateManual,
                      icon: _isLoading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.attach_money),
                      label: Text(_isLoading ? 'Estimating...' : 'Estimate Price'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        backgroundColor: theme.primaryColor,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_error != null) _buildError(),
          if (_result != null) _buildResult(theme),
        ],
      ),
    );
  }

  Widget _buildVinTab(ThemeData theme) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Enter VIN',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('We\'ll decode the VIN and estimate the fair market value.',
                      style: TextStyle(color: Colors.grey)),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _vinController,
                    maxLength: 17,
                    textCapitalization: TextCapitalization.characters,
                    decoration: InputDecoration(
                      hintText: '17-character VIN',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      prefixIcon: const Icon(Icons.qr_code),
                    ),
                    onSubmitted: (_) => _estimateByVin(),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : _estimateByVin,
                      icon: _isLoading
                          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                          : const Icon(Icons.attach_money),
                      label: Text(_isLoading ? 'Estimating...' : 'Estimate by VIN'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        backgroundColor: theme.primaryColor,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_error != null) _buildError(),
          if (_result != null) _buildResult(theme),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Padding(
      padding: const EdgeInsets.only(top: 16),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.red.shade50,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.red.shade200),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: Colors.red),
            const SizedBox(width: 8),
            Expanded(child: Text(_error!, style: TextStyle(color: Colors.red.shade900))),
          ],
        ),
      ),
    );
  }

  Widget _buildResult(ThemeData theme) {
    final r = _result!;
    return Padding(
      padding: const EdgeInsets.only(top: 20),
      child: Column(
        children: [
          // Price range card
          Card(
            elevation: 3,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            color: theme.primaryColor,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    '${r.year ?? ''} ${r.make ?? ''} ${r.model ?? ''}'.trim(),
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '\$${r.marketPrice?.toStringAsFixed(0) ?? 'N/A'}',
                    style: const TextStyle(fontSize: 36, fontWeight: FontWeight.bold, color: Colors.white),
                  ),
                  const SizedBox(height: 4),
                  Text('Estimated Market Value', style: TextStyle(color: Colors.white.withOpacity(0.8))),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _priceColumn('\$${r.lowPrice?.toStringAsFixed(0) ?? '-'}', 'Low'),
                      Container(height: 30, width: 1, color: Colors.white.withOpacity(0.3)),
                      _priceColumn('\$${r.marketPrice?.toStringAsFixed(0) ?? '-'}', 'Market'),
                      Container(height: 30, width: 1, color: Colors.white.withOpacity(0.3)),
                      _priceColumn('\$${r.highPrice?.toStringAsFixed(0) ?? '-'}', 'High'),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'Confidence: ${((r.confidence ?? 0) * 100).toStringAsFixed(0)}%',
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Details card
          const SizedBox(height: 12),
          Card(
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Details', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  const Divider(),
                  if (r.msrp != null)
                    _detailRow('Original MSRP', '\$${r.msrp!.toStringAsFixed(0)}'),
                  if (r.mileage != null)
                    _detailRow('Mileage', '${r.mileage!.toStringAsFixed(0)} mi'),
                  if (r.condition != null)
                    _detailRow('Condition', r.condition!.substring(0, 1).toUpperCase() + r.condition!.substring(1)),
                  if (r.source != null)
                    _detailRow('Source', r.source!.replaceAll('_', ' ')),
                ],
              ),
            ),
          ),

          // Notes
          if (r.notes.isNotEmpty) ...[
            const SizedBox(height: 12),
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Notes', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const Divider(),
                    ...r.notes.map((n) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.info_outline, size: 16, color: Colors.grey.shade600),
                          const SizedBox(width: 8),
                          Expanded(child: Text(n, style: const TextStyle(fontSize: 13))),
                        ],
                      ),
                    )),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _priceColumn(String price, String label) {
    return Column(
      children: [
        Text(price, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white)),
        const SizedBox(height: 2),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.7))),
      ],
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade600)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
