/*
    safe_divide(numerator, denominator)
    Returns numerator / denominator.
    Returns NULL instead of raising division-by-zero when denominator = 0 or NULL.

    Usage:
        {{ safe_divide('sum(revenue)', 'count(*)') }}
        {{ safe_divide('successful_count * 100.0', 'total_count') }}
*/

{% macro safe_divide(numerator, denominator) %}
    iff(
        ({{ denominator }}) = 0 or ({{ denominator }}) is null,
        null,
        ({{ numerator }}) / ({{ denominator }})
    )
{% endmacro %}
