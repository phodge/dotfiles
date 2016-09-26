<?php

function debug_txt($value, $indent = '', $seen = array()) {
    if ($value === null)
        return 'NULL';
    if ($value === true)
        return 'TRUE';
    if ($value === false)
        return 'FALSE';

    if (is_int($value) || is_float($value))
        return "$value";

    if (is_string($value)) {
        // can it be shown with just single-quotes?
        if(preg_match('/\A[\w !@#$%^&*()\[\]{}\-=+:;,.<>|\\\\]*\z/', $value))
            return "'" . str_replace('\\', '\\\\', $value) . "'";

        // turn it into a fancy string
        $inner = '';
        $replace = array(
            "\\" => '\\\\',
            "\t" => '\\t',
            "\n" => '\\n',
            "\r" => '\\r',
        );
        $value = str_replace(array_keys($replace), array_values($replace), $value);
        // handle chars outside of printable ascii range
        for ($i = 0; $i < strlen($value); ++$i) {
            $char = $value[$i];
            if (ord($char) > ord('~'))
                $inner .= '\\x' . strtoupper(dechex(ord($char)));
            else
                $inner .= $char;
        }
        return '"' . $inner . '"';
    }

    if (is_array($value)) {
        if (count($value) === 0) {
            return 'array()';
        }

        if (array_keys($value) === range(0, count($value) - 1)) {
            // TODO: numerical array
            // build array of inner values
            $inner = array();
            $have_nl = false;
            $inner_len = 0;
            foreach ($value as $array_value) {
                $inner_txt = debug_txt($array_value, "$indent  ", $seen);
                $inner_len += strlen($inner_txt) + 2;
                if (!$have_nl)
                    $have_nl = false !== strpos($inner_txt, "\n");
                $inner[] = $inner_txt;
            }
            return ($inner_len < 60 && !$have_nl)
                    ? "array(" . implode(", ", $inner) . ")"
                    : "array(\n  $indent" . implode(",\n  $indent", $inner) . ",\n$indent)";
        }

        // TODO: hash table
        $inner_len = 0;
        $have_nl   = false;
        $keys  = array();
        $items = array();
        foreach (array_keys($value) as $key) {
            $key_txt  = debug_txt($key);
            $item_txt = debug_txt($value[$key], "$indent  ", $seen);
            $keys[]  = $key_txt;
            $items[] = $item_txt;

            if (!$have_nl)
                $have_nl = false !== strpos($item_txt, "\n");
            $inner_len += strlen($key_txt) + 4 + strlen($item_txt) + 2;
        }

        // decide whether to display everything on one line, or on separate lines
        if ($inner_len < 60 && !$have_nl) {
            // all on one line
            $inner = array();
            foreach ($keys as $i => $key_txt)
                $inner[] = $key_txt .' => ' . $items[$i];
            return 'array(' . implode(', ', $inner) . ')';
        }

        $pad_len = max(array_map('strlen', $keys));
        $inner   = array();
        foreach ($keys as $i => $key_txt)
            $inner[] = str_pad($key_txt, $pad_len, ' ', STR_PAD_RIGHT) . ' => ' . $items[$i] . ',';
        return "array(\n  $indent" . implode("\n  $indent", $inner) . "\n$indent)";
    }

    if (is_object($value)) {
        // if we have already seen this instance before, it is recursion
        foreach ($seen as $prior_object) {
            if ($value === $prior_object)
                return "[Recursion: " . get_class($value) . "]";
        }
        $seen[]  = $value;

        $properties = array();
        foreach ($value as $prop_name => $prop_value) {
            $properties[$prop_name] = debug_txt($prop_value, "$indent  ", $seen);
        }

        // very simple if it has no properties
        if (count($properties) === 0)
            return get_class($value) . ' {}';

        $inner   = array();
        $pad_len = max(array_map('strlen', array_keys($properties)));
        foreach ($properties as $prop_name => $prop_txt)
            $inner[] = '->' . str_pad($prop_name, $pad_len, ' ', STR_PAD_RIGHT) . ' = ' . $prop_txt;
        return get_class($value) . " {\n  $indent" . implode("\n  $indent", $inner) . "\n$indent}";
    }

    return '[TODO: ' . gettype($value) . ']';
}

