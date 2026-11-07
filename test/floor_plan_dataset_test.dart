import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:town_pass/page/photo_navigation/model/floor_plan_dataset.dart';

void main() {
  late FloorPlanDataset dataset;

  setUpAll(() {
    dataset = FloorPlanDataset.fromJsonString(
      File(
        'assets/floorplans/taipei_main_station/manifest.json',
      ).readAsStringSync(),
    );
  });

  test('loads all four floors and reviewed graph data', () {
    expect(dataset.floors.map((floor) => floor.id), ['B1', 'B2', 'B3', 'B4']);
    expect(dataset.nodes, isNotEmpty);
    expect(dataset.destinations, hasLength(2));
  });

  test('finds a route from M4 to the Bannan Line platform', () {
    final route = dataset.shortestPath('b1_m4_entry', 'b3_bl_platform');

    expect(route.first.id, 'b1_m4_entry');
    expect(route.last.id, 'b3_bl_platform');
  });

  test('accessible route avoids stair nodes', () {
    final route = dataset.shortestPath(
      'b1_m4_entry',
      'b4_r_platform',
      accessibleOnly: true,
    );

    expect(route, isNotEmpty);
    expect(route.where((node) => node.kind == 'stairs'), isEmpty);
    expect(route.map((node) => node.id), contains('b4_r_elevator'));
  });
}
