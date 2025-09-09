import Foundation
import Vision
import ImageIO

struct RecognitionResult: Codable {
    let text: String
    let boundingBox: [Double]
    let confidence: Float
}

func loadCGImage(from url: URL) -> CGImage? {
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { return nil }
    return CGImageSourceCreateImageAtIndex(src, 0, nil)
}

func recognizeText(in image: CGImage, languages: [String]) throws -> [RecognitionResult] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    if !languages.isEmpty {
        request.recognitionLanguages = languages
    }

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])

    guard let observations = request.results as? [VNRecognizedTextObservation] else {
        return []
    }

    return observations.compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        let boundingBox = [Double(box.origin.x), Double(box.origin.y), Double(box.size.width), Double(box.size.height)]
        return RecognitionResult(text: candidate.string, boundingBox: boundingBox, confidence: candidate.confidence)
    }
}

func main() throws {
    guard CommandLine.arguments.count > 1 else {
        throw NSError(domain: "VisionSwift", code: 1, userInfo: [NSLocalizedDescriptionKey: "Image path missing"])
    }

    let imageURL = URL(fileURLWithPath: CommandLine.arguments[1])
    let languages = Array(CommandLine.arguments.dropFirst(2))
    guard let image = loadCGImage(from: imageURL) else {
        throw NSError(domain: "VisionSwift", code: 2, userInfo: [NSLocalizedDescriptionKey: "Unable to load image"])
    }

    let results = try recognizeText(in: image, languages: languages)
    let encoder = JSONEncoder()
    encoder.outputFormatting = .prettyPrinted
    let data = try encoder.encode(results)
    if let json = String(data: data, encoding: .utf8) {
        print(json)
    }
}

try main()
