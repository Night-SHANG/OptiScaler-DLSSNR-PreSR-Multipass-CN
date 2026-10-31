#pragma once
// Display-only status localization. Never writes to renderer state or logs.
#include <string>
#include <string_view>
#include <vector>

namespace OptiScalerCN::Status
{
struct Entry { const char* source; const char* text; bool pattern; };

inline bool Match(std::string_view input, std::string_view pattern, std::vector<std::string_view>& values)
{
    values.clear();
    std::size_t at = 0, p = 0;
    while (true)
    {
        const auto hole = pattern.find("{}", p);
        const auto literal = pattern.substr(p, hole == std::string_view::npos ? hole : hole - p);
        if (input.substr(at, literal.size()) != literal) return false;
        at += literal.size();
        if (hole == std::string_view::npos) return at == input.size();
        p = hole + 2;
        const auto nextHole = pattern.find("{}", p);
        const auto nextLiteral = pattern.substr(p, nextHole == std::string_view::npos ? nextHole : nextHole - p);
        if (nextLiteral.empty() && nextHole != std::string_view::npos) return false;
        const auto end = nextLiteral.empty() ? input.size() : input.find(nextLiteral, at);
        if (end == std::string_view::npos || end == at) return false;
        values.push_back(input.substr(at, end - at));
        at = end;
    }
}

template<std::size_t N>
std::string Translate(std::string_view input, const Entry (&entries)[N], bool chinese = true, unsigned depth = 0)
{
    if (!chinese || depth > 2) return std::string(input);
    for (const auto& entry : entries)
        if (!entry.pattern && input == entry.source) return entry.text;
    for (const auto& entry : entries)
    {
        if (!entry.pattern) continue;
        std::vector<std::string_view> values;
        if (!Match(input, entry.source, values)) continue;
        std::string output;
        std::string_view translated(entry.text);
        std::size_t at = 0, value = 0;
        while (true)
        {
            const auto hole = translated.find("{}", at);
            output += translated.substr(at, hole == std::string_view::npos ? hole : hole - at);
            if (hole == std::string_view::npos) break;
            if (value >= values.size()) return std::string(input);
            output += values[value++]; // Runtime parameters stay byte-for-byte unchanged.
            at = hole + 2;
        }
        if (value == values.size()) return output;
    }
    return std::string(input);
}
} // namespace OptiScalerCN::Status
