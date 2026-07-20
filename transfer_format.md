// This format is used for graph transfer to/from Godot:

{
	"directed": true,
	"edges": [
		{
			"source": "40",
			"target": "45"
		},
		{
			"source": "45",
			"target": "50"
		}
	],
	"multigraph": false,
	"nodes": [
		{
			"id": "40",
			"type": "Image to Text"
		},
		{
			"id": "45",
			"type": "Text to Text"
		},
		{
			"id": "50",
			"type": "Text to Text"
		}
	]
}

// --------NETWORKX----------

{
	"directed": True,
	"multigraph": False,
	"graph": {},
	"nodes": [
				{"id": "A"},
				{"id": "B"},
				{"id": "C"}
			],
	"edges": [
				{"source": "A","target": "B"},
				{"source": "B", "target": "C"}
			]
}

