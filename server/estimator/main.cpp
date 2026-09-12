// SPDX-License-Identifier: GPL-2.0-or-later
#include "LoopTempoEstimator/LoopTempoEstimator.h"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

namespace {

class WavReader final : public LTE::LteAudioReader
{
public:
    bool load(const std::string& path)
    {
        std::ifstream file(path, std::ios::binary);
        if (!file)
        {
            return false;
        }
        char riff[12];
        if (!file.read(riff, 12) || std::memcmp(riff, "RIFF", 4) != 0
            || std::memcmp(riff + 8, "WAVE", 4) != 0)
        {
            return false;
        }
        uint16_t audioFormat = 0;
        uint16_t channels = 0;
        uint32_t sampleRate = 0;
        uint16_t bitsPerSample = 0;
        std::vector<char> data;
        while (file)
        {
            char header[8];
            if (!file.read(header, 8))
            {
                break;
            }
            const uint32_t size = readU32(header + 4);
            if (std::memcmp(header, "fmt ", 4) == 0)
            {
                std::vector<char> fmt(size);
                if (!file.read(fmt.data(), size))
                {
                    return false;
                }
                if (size < 16)
                {
                    return false;
                }
                audioFormat = readU16(fmt.data());
                channels = readU16(fmt.data() + 2);
                sampleRate = readU32(fmt.data() + 4);
                bitsPerSample = readU16(fmt.data() + 14);
                if (size % 2 == 1)
                {
                    file.ignore(1);
                }
                continue;
            }
            if (std::memcmp(header, "data", 4) == 0)
            {
                data.resize(size);
                if (!file.read(data.data(), size))
                {
                    return false;
                }
                break;
            }
            file.ignore(size + (size % 2));
        }
        if (audioFormat != 1 || channels == 0 || sampleRate == 0 || bitsPerSample != 16
            || data.empty())
        {
            return false;
        }
        const size_t frameCount = data.size() / (channels * 2);
        samples_.resize(frameCount);
        const auto* frames = reinterpret_cast<const int16_t*>(data.data());
        for (size_t i = 0; i < frameCount; ++i)
        {
            float sum = 0.f;
            for (uint16_t channel = 0; channel < channels; ++channel)
            {
                sum += static_cast<float>(frames[i * channels + channel]) / 32768.f;
            }
            samples_[i] = sum / static_cast<float>(channels);
        }
        sampleRate_ = static_cast<double>(sampleRate);
        return true;
    }

    double GetSampleRate() const override
    {
        return sampleRate_;
    }

    long long GetNumSamples() const override
    {
        return static_cast<long long>(samples_.size());
    }

    void ReadFloats(float* buffer, long long where, size_t numFrames) const override
    {
        for (size_t i = 0; i < numFrames; ++i)
        {
            const auto index = static_cast<size_t>(where) + i;
            buffer[i] = index < samples_.size() ? samples_[index] : 0.f;
        }
    }

private:
    static uint16_t readU16(const char* bytes)
    {
        return static_cast<uint8_t>(bytes[0]) | (static_cast<uint16_t>(static_cast<uint8_t>(bytes[1])) << 8);
    }

    static uint32_t readU32(const char* bytes)
    {
        return static_cast<uint8_t>(bytes[0])
            | (static_cast<uint32_t>(static_cast<uint8_t>(bytes[1])) << 8)
            | (static_cast<uint32_t>(static_cast<uint8_t>(bytes[2])) << 16)
            | (static_cast<uint32_t>(static_cast<uint8_t>(bytes[3])) << 24);
    }

    double sampleRate_ = 0;
    std::vector<float> samples_;
};

} // namespace

int main(int argc, char** argv)
{
    if (argc != 2)
    {
        std::cerr << "usage: armarium-loop-tempo <wav>\n";
        return 2;
    }
    WavReader reader;
    if (!reader.load(argv[1]))
    {
        std::cerr << "unable to read wav\n";
        return 1;
    }
    const auto bpm = LTE::GetBpm(
        reader, LTE::FalsePositiveTolerance::Lenient, [](double) {});
    if (bpm.has_value())
    {
        std::cout << "{\"loop\":true,\"bpm\":" << *bpm << "}\n";
        return 0;
    }
    std::cout << "{\"loop\":false}\n";
    return 0;
}
