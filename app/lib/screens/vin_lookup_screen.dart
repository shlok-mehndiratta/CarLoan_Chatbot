import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/contract_model.dart';

class VinLookupScreen extends StatefulWidget {
  const VinLookupScreen({super.key});

  @override
  State<VinLookupScreen> createState() => _VinLookupScreenState();
}

class _VinLookupScreenState extends State<VinLookupScreen> {
  final TextEditingController _vinController = TextEditingController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  VehicleInfo? _vehicleInfo;
  String? _errorMessage;

  Future<void> _lookupVin() async {
    final vin = _vinController.text.trim().toUpperCase();
    if (vin.length != 17) {
      setState(() => _errorMessage = 'VIN must be exactly 17 characters');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _vehicleInfo = null;
    });

    try {
      final info = await _apiService.getVehicleInfo(vin);
      setState(() => _vehicleInfo = info);
    } catch (e) {
      setState(() => _errorMessage = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  void dispose() {
    _vinController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('VIN Lookup'),
        centerTitle: true,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Search Card
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.directions_car, color: theme.primaryColor, size: 28),
                        const SizedBox(width: 12),
                        Text(
                          'Vehicle Identification Number',
                          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _vinController,
                      maxLength: 17,
                      textCapitalization: TextCapitalization.characters,
                      decoration: InputDecoration(
                        hintText: 'Enter 17-character VIN',
                        prefixIcon: const Icon(Icons.search),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                        counterText: '${_vinController.text.length}/17',
                        suffixIcon: _vinController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear),
                                onPressed: () => setState(() => _vinController.clear()),
                              )
                            : null,
                      ),
                      onChanged: (_) => setState(() {}),
                      onSubmitted: (_) => _lookupVin(),
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isLoading ? null : _lookupVin,
                        icon: _isLoading
                            ? const SizedBox(
                                width: 18, height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Icon(Icons.search),
                        label: Text(_isLoading ? 'Looking up...' : 'Lookup VIN'),
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

            // Error
            if (_errorMessage != null) ...[
              const SizedBox(height: 16),
              Container(
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
                    Expanded(child: Text(_errorMessage!, style: TextStyle(color: Colors.red.shade900))),
                  ],
                ),
              ),
            ],

            // Results
            if (_vehicleInfo != null) ...[
              const SizedBox(height: 20),
              _buildVehicleHeader(theme),
              const SizedBox(height: 16),
              _buildSpecsCard(theme, isDark),
              if (_vehicleInfo!.recalls.isNotEmpty) ...[
                const SizedBox(height: 16),
                _buildRecallsCard(theme),
              ],
              if (_vehicleInfo!.complaintsCount > 0) ...[
                const SizedBox(height: 16),
                _buildComplaintsCard(theme),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildVehicleHeader(ThemeData theme) {
    final v = _vehicleInfo!;
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      color: theme.primaryColor,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${v.year ?? ''} ${v.make ?? ''} ${v.model ?? ''}'.trim(),
              style: const TextStyle(
                fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white,
              ),
            ),
            if (v.trim != null) ...[
              const SizedBox(height: 4),
              Text(v.trim!, style: TextStyle(fontSize: 16, color: Colors.white.withOpacity(0.85))),
            ],
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.2),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                'VIN: ${v.vin}',
                style: const TextStyle(color: Colors.white, fontSize: 12, fontFamily: 'monospace'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSpecsCard(ThemeData theme, bool isDark) {
    final v = _vehicleInfo!;
    final specs = <MapEntry<String, String>>[];

    if (v.bodyClass != null) specs.add(MapEntry('Body', v.bodyClass!));
    if (v.engineType != null) specs.add(MapEntry('Engine', v.engineType!));
    if (v.fuelType != null) specs.add(MapEntry('Fuel', v.fuelType!));
    if (v.driveType != null) specs.add(MapEntry('Drive', v.driveType!));
    if (v.transmission != null) specs.add(MapEntry('Trans.', v.transmission!));
    if (v.cylinders != null) specs.add(MapEntry('Cylinders', v.cylinders.toString()));
    if (v.manufacturer != null) specs.add(MapEntry('Manufacturer', v.manufacturer!));

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Specifications', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const Divider(),
            ...specs.map((spec) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 6),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(spec.key, style: TextStyle(color: Colors.grey.shade600)),
                  Flexible(
                    child: Text(
                      spec.value,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                      textAlign: TextAlign.right,
                    ),
                  ),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildRecallsCard(ThemeData theme) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.warning_amber, color: Colors.orange, size: 22),
                const SizedBox(width: 8),
                Text(
                  'Recalls (${_vehicleInfo!.recalls.length})',
                  style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(),
            ..._vehicleInfo!.recalls.map((recall) => Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.orange.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.orange.shade200),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    recall.campaignNumber,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  Text(recall.component, style: TextStyle(color: Colors.orange.shade900, fontSize: 13)),
                  const SizedBox(height: 4),
                  Text(recall.summary, style: const TextStyle(fontSize: 12)),
                ],
              ),
            )),
          ],
        ),
      ),
    );
  }

  Widget _buildComplaintsCard(ThemeData theme) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const Icon(Icons.feedback, color: Colors.blue, size: 22),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('NHTSA Complaints', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                  Text('${_vehicleInfo!.complaintsCount} complaints on file'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
