import 'dart:convert';

import 'package:flutter/services.dart';

class FloorPlanDataset {
  const FloorPlanDataset({
    required this.stationId,
    required this.reviewStatus,
    required this.floors,
    required this.nodes,
    required this.edges,
    required this.destinations,
  });

  final String stationId;
  final String reviewStatus;
  final List<FloorPlanFloor> floors;
  final Map<String, FloorPlanNode> nodes;
  final List<FloorPlanEdge> edges;
  final List<FloorPlanDestination> destinations;

  static const assetPath =
      'assets/floorplans/taipei_main_station/manifest.json';

  static Future<FloorPlanDataset> loadFromAssets({AssetBundle? bundle}) async {
    return FloorPlanDataset.fromJsonString(
      await (bundle ?? rootBundle).loadString(assetPath),
    );
  }

  factory FloorPlanDataset.fromJsonString(String source) {
    return FloorPlanDataset.fromJson(
      jsonDecode(source) as Map<String, dynamic>,
    );
  }

  factory FloorPlanDataset.fromJson(Map<String, dynamic> json) {
    final nodeList = (json['nodes'] as List<dynamic>)
        .map((item) => FloorPlanNode.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
    return FloorPlanDataset(
      stationId: json['stationId'] as String,
      reviewStatus: json['reviewStatus'] as String,
      floors: (json['floors'] as List<dynamic>)
          .map((item) => FloorPlanFloor.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      nodes: {for (final node in nodeList) node.id: node},
      edges: (json['edges'] as List<dynamic>)
          .map((item) => FloorPlanEdge.fromJson(item as Map<String, dynamic>))
          .toList(growable: false),
      destinations: (json['destinations'] as List<dynamic>)
          .map(
            (item) =>
                FloorPlanDestination.fromJson(item as Map<String, dynamic>),
          )
          .toList(growable: false),
    );
  }

  /// Dijkstra over the reviewed semantic graph. Pixel masks are not used as
  /// routing truth because the source PDF is a labelled raster illustration.
  List<FloorPlanNode> shortestPath(
    String startNodeId,
    String endNodeId, {
    bool accessibleOnly = false,
  }) {
    if (!nodes.containsKey(startNodeId) || !nodes.containsKey(endNodeId)) {
      throw ArgumentError('Unknown start or end node');
    }

    final distances = <String, double>{
      for (final id in nodes.keys) id: double.infinity,
      startNodeId: 0,
    };
    final previous = <String, String>{};
    final unvisited = nodes.keys.toSet();

    while (unvisited.isNotEmpty) {
      String? current;
      var smallestDistance = double.infinity;
      for (final candidate in unvisited) {
        final distance = distances[candidate]!;
        if (distance < smallestDistance) {
          current = candidate;
          smallestDistance = distance;
        }
      }
      if (current == null || smallestDistance == double.infinity) break;
      if (current == endNodeId) break;
      unvisited.remove(current);

      for (final edge in edges) {
        if (accessibleOnly && !edge.accessible) continue;
        final neighbour = edge.neighbourOf(current);
        if (neighbour == null || !unvisited.contains(neighbour)) continue;
        final candidateDistance = smallestDistance + edge.cost;
        if (candidateDistance < distances[neighbour]!) {
          distances[neighbour] = candidateDistance;
          previous[neighbour] = current;
        }
      }
    }

    if (startNodeId != endNodeId && !previous.containsKey(endNodeId)) {
      return const [];
    }
    final path = <FloorPlanNode>[nodes[endNodeId]!];
    var cursor = endNodeId;
    while (cursor != startNodeId) {
      cursor = previous[cursor]!;
      path.add(nodes[cursor]!);
    }
    return path.reversed.toList(growable: false);
  }
}

class FloorPlanFloor {
  const FloorPlanFloor({
    required this.id,
    required this.label,
    required this.image,
    required this.walkableMask,
    required this.width,
    required this.height,
  });

  final String id;
  final String label;
  final String image;
  final String walkableMask;
  final int width;
  final int height;

  factory FloorPlanFloor.fromJson(Map<String, dynamic> json) => FloorPlanFloor(
    id: json['id'] as String,
    label: json['label'] as String,
    image: json['image'] as String,
    walkableMask: json['walkableMask'] as String,
    width: json['width'] as int,
    height: json['height'] as int,
  );
}

class FloorPlanNode {
  const FloorPlanNode({
    required this.id,
    required this.floorId,
    required this.kind,
    required this.x,
    required this.y,
    required this.names,
    required this.verified,
  });

  final String id;
  final String floorId;
  final String kind;
  final double x;
  final double y;
  final Map<String, String> names;
  final bool verified;

  factory FloorPlanNode.fromJson(Map<String, dynamic> json) {
    final position = json['position'] as Map<String, dynamic>;
    return FloorPlanNode(
      id: json['id'] as String,
      floorId: json['floorId'] as String,
      kind: json['kind'] as String,
      x: (position['x'] as num).toDouble(),
      y: (position['y'] as num).toDouble(),
      names: (json['names'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, value as String),
      ),
      verified: json['verified'] as bool,
    );
  }
}

class FloorPlanEdge {
  const FloorPlanEdge({
    required this.id,
    required this.from,
    required this.to,
    required this.kind,
    required this.cost,
    required this.accessible,
    required this.bidirectional,
  });

  final String id;
  final String from;
  final String to;
  final String kind;
  final double cost;
  final bool accessible;
  final bool bidirectional;

  factory FloorPlanEdge.fromJson(Map<String, dynamic> json) => FloorPlanEdge(
    id: json['id'] as String,
    from: json['from'] as String,
    to: json['to'] as String,
    kind: json['kind'] as String,
    cost: (json['cost'] as num).toDouble(),
    accessible: json['accessible'] as bool,
    bidirectional: json['bidirectional'] as bool,
  );

  String? neighbourOf(String nodeId) {
    if (from == nodeId) return to;
    if (bidirectional && to == nodeId) return from;
    return null;
  }
}

class FloorPlanDestination {
  const FloorPlanDestination({
    required this.id,
    required this.nodeId,
    required this.names,
    required this.aliases,
  });

  final String id;
  final String nodeId;
  final Map<String, String> names;
  final List<String> aliases;

  factory FloorPlanDestination.fromJson(Map<String, dynamic> json) =>
      FloorPlanDestination(
        id: json['id'] as String,
        nodeId: json['nodeId'] as String,
        names: (json['names'] as Map<String, dynamic>).map(
          (key, value) => MapEntry(key, value as String),
        ),
        aliases: (json['aliases'] as List<dynamic>).cast<String>(),
      );
}
