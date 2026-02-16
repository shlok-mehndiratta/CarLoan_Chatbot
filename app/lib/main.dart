import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'screens/home_screen.dart';
import 'screens/vin_lookup_screen.dart';
import 'screens/price_estimation_screen.dart';
import 'screens/comparison_dashboard_screen.dart';
import 'models/contract_model.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Car Contract AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      darkTheme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _currentIndex = 0;
  ContractAnalysis? _lastAnalysis;

  void _onAnalysisComplete(ContractAnalysis analysis) {
    setState(() {
      _lastAnalysis = analysis;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      HomeScreen(onAnalysisComplete: _onAnalysisComplete),
      const VinLookupScreen(),
      const PriceEstimationScreen(),
      ComparisonDashboardScreen(lastAnalysis: _lastAnalysis),
    ];

    return DefaultTabController(
      length: 4,
      child: Builder(
        builder: (context) {
          // Sync tab controller with our index
          final tabController = DefaultTabController.of(context);
          tabController.addListener(() {
            if (!tabController.indexIsChanging) {
              setState(() => _currentIndex = tabController.index);
            }
          });

          return Scaffold(
            body: TabBarView(
              controller: tabController,
              physics: const NeverScrollableScrollPhysics(),
              children: screens,
            ),
            bottomNavigationBar: NavigationBar(
              selectedIndex: _currentIndex,
              onDestinationSelected: (index) {
                tabController.animateTo(index);
                setState(() => _currentIndex = index);
              },
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.upload_file_outlined),
                  selectedIcon: Icon(Icons.upload_file),
                  label: 'Analyze',
                ),
                NavigationDestination(
                  icon: Icon(Icons.directions_car_outlined),
                  selectedIcon: Icon(Icons.directions_car),
                  label: 'VIN',
                ),
                NavigationDestination(
                  icon: Icon(Icons.attach_money_outlined),
                  selectedIcon: Icon(Icons.attach_money),
                  label: 'Price',
                ),
                NavigationDestination(
                  icon: Icon(Icons.dashboard_outlined),
                  selectedIcon: Icon(Icons.dashboard),
                  label: 'Dashboard',
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}