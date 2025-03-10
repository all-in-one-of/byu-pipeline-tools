import nuke

def go():
	nodes = nuke.selectedNodes()
	leafNodes = []
	for node in nodes:
		if node.Class() == 'Read':
			channels = node.channels()
			layers = list( set([channel.split('.')[0] for channel in channels]) )
			layers.sort()

			count = 0
			for layer in layers:
				if '_lgt' in layer:
					shuffleNode = nuke.nodes.Shuffle(label=layer,inputs=[node])
					shuffleNode['in'].setValue( layer )
					shuffleNode['postage_stamp'].setValue(True)
					unpremultNode = nuke.nodes.Unpremult(label=layer,inputs=[shuffleNode])
					colorCorrectNode = nuke.nodes.ColorCorrect(label=layer,inputs=[unpremultNode])
					hueShiftNode = nuke.nodes.HueShift(label=layer,inputs=[colorCorrectNode])
					premultNode = nuke.nodes.Premult(label=layer,inputs=[hueShiftNode])
					if count == 0:
						leafNodes.append(premultNode)
					if count > 0:
						merge = nuke.nodes.Merge(operation='plus',inputs=[premultNode,leafNodes[count-1]])
						leafNodes.append(merge)
					count = count + 1
		else:
			pass
